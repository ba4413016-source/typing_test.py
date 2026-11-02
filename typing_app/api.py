from __future__ import annotations

import hashlib
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, delete, desc, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import Settings
from .database import initialize_database, make_engine, make_session_factory
from .game_engine import generate_target, score_attempt
from .models import (
    Attempt,
    Block,
    Challenge,
    ChallengeParticipant,
    Follow,
    GameSuggestion,
    LoginSession,
    Media,
    Message,
    Notification,
    PracticeRound,
    User,
    utcnow,
    uid,
)
from .security import (
    RateLimiter,
    aware,
    clean_text,
    digest_token,
    normalize_username,
    normalized_avatar,
    opaque_token,
    password_hash,
    password_matches,
    same_origin,
    social_handle,
    validate_password,
)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(Input):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=40)


class ProfileInput(Input):
    display_name: str = Field(min_length=1, max_length=40)
    instagram: str = Field(default="", max_length=100)
    snapchat: str = Field(default="", max_length=100)
    twitter: str = Field(default="", max_length=100)


class BotInput(Input):
    name: str = Field(min_length=1, max_length=40)


class RoundInput(Input):
    game: str = Field(min_length=1, max_length=12)
    difficulty: str = Field(min_length=1, max_length=12)
    language: str = Field(min_length=2, max_length=2)
    count: int | None = Field(default=None, ge=1, le=20)


class MessageInput(Input):
    body: str = Field(min_length=1, max_length=2000)


class ReadInput(Input):
    ids: list[int] | None = Field(default=None, max_length=500)


class ChallengeInput(RoundInput):
    visibility: str
    max_players: int = Field(ge=2, le=8)


class SuggestionInput(Input):
    title: str = Field(min_length=1, max_length=80)
    body: str = Field(min_length=1, max_length=2000)


class ReviewInput(Input):
    status: str
    admin_note: str = Field(default="", max_length=500)


class SubmitInput(Input):
    text: str = Field(max_length=1200)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return aware(dt).isoformat().replace("+00:00", "Z")


def db_session(request: Request):
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def fail(status: int, code: str, en: str, ar: str | None = None):
    translations = {
        "auth_required": "سجّل دخولك أولًا.",
        "csrf": "تعذر التحقق من الجلسة. حدّث الصفحة وحاول مجددًا.",
        "invalid_credentials": "اسم المستخدم أو كلمة المرور غير صحيحة.",
        "username_taken": "اسم المستخدم مستخدم بالفعل؛ اختر اسمًا آخر.",
        "reserved_username": "اسم المستخدم محجوز لإدارة المنصة.",
        "invalid_input": "تحقق من اليوزر وكلمة المرور: 3–24 حرفًا إنجليزيًا أو رقمًا أو نقطة أو شرطة سفلية، وكلمة المرور 10 أحرف على الأقل.",
        "invalid_profile": "تحقق من الاسم الظاهر ويوزرات التواصل؛ أدخل اليوزر دون رابط.",
        "invalid_avatar": "اختر صورة JPEG أو PNG أو WebP صالحة، لا تتجاوز 2MB و4096×4096.",
        "blocked": "هذه العملية غير متاحة بسبب الحظر.",
        "round_closed": "أُرسلت هذه الجولة أو أُوقفت بالفعل.",
        "challenge_closed": "هذا التحدي مغلق أو انتهت صلاحية دعوته.",
        "challenge_full": "اكتمل عدد المشاركين في التحدي.",
        "challenge_not_active": "التحدي لا يستقبل إجابات الآن.",
        "not_enough_players": "يلزم انضمام لاعبين على الأقل لبدء التحدي.",
        "owner_only": "هذا الإجراء متاح لمنشئ التحدي فقط.",
        "admin_required": "هذا القسم متاح لمدير المنصة فقط.",
    }
    raise HTTPException(
        status, {"code": code, "en": en, "ar": ar or translations.get(code, en)}
    )


def get_session_user(
    request: Request, db: Session
) -> tuple[User | None, LoginSession | None]:
    raw = request.cookies.get("mt_session")
    if not raw:
        return None, None
    row = db.get(LoginSession, digest_token(raw))
    if not row or aware(row.expires_at) <= utcnow():
        return None, None
    user = db.get(User, row.user_id)
    return (user, row) if user else (None, None)


def require_user(request: Request, db: Session) -> tuple[User, LoginSession]:
    user, sess = get_session_user(request, db)
    if not user or not sess:
        fail(401, "auth_required", "Sign in required.")
    return user, sess


def mutation_guard(request: Request, user: User, sess: LoginSession):
    same_origin(request)
    supplied = request.headers.get("x-csrf-token", "")
    if not secrets.compare_digest(supplied, sess.csrf_token):
        fail(403, "csrf", "A valid CSRF token is required.")
    if not request.app.state.settings.testing:
        limiter = request.app.state.limiter
        ip = request.client.host if request.client else "unknown"
        limiter.check(f"write-ip:{ip}", 300, 60)
        limiter.check(f"write-user:{user.id}", 300, 60)


def lite(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": f"/media/{user.avatar_id}" if user.avatar_id else None,
    }


def stats(db: Session, user_id: str) -> dict[str, Any]:
    row = db.execute(
        select(
            func.count(Attempt.id),
            func.coalesce(func.sum(Attempt.points), 0),
            func.coalesce(func.max(Attempt.wpm), 0),
            func.coalesce(func.avg(Attempt.accuracy), 0),
        ).where(Attempt.user_id == user_id, Attempt.eligible.is_(True))
    ).one()
    total = (
        db.scalar(select(func.count(Attempt.id)).where(Attempt.user_id == user_id)) or 0
    )
    accuracy = (
        db.scalar(select(func.avg(Attempt.accuracy)).where(Attempt.user_id == user_id))
        or 0
    )
    return {
        "rounds": total,
        "total_points": int(row[1] or 0),
        "best_wpm": round(float(row[2] or 0), 2),
        "accuracy": round(float(accuracy), 2),
    }


def is_blocked(db: Session, a: str, b: str) -> bool:
    return (
        db.scalar(
            select(Block.blocker_id)
            .where(
                or_(
                    and_(Block.blocker_id == a, Block.blocked_id == b),
                    and_(Block.blocker_id == b, Block.blocked_id == a),
                )
            )
            .limit(1)
        )
        is not None
    )


def lock_user_pair(db: Session, a: str, b: str):
    """Serialize relationship and message mutations for one unordered user pair."""
    db.scalars(
        select(User)
        .where(User.id.in_(sorted((a, b))))
        .order_by(User.id)
        .with_for_update()
    ).all()


def unread_message_count(
    db: Session, recipient_id: str, sender_id: str | None = None
) -> int:
    blocked_pair = (
        ~select(Block.blocker_id)
        .where(
            or_(
                and_(
                    Block.blocker_id == Message.sender_id,
                    Block.blocked_id == Message.recipient_id,
                ),
                and_(
                    Block.blocker_id == Message.recipient_id,
                    Block.blocked_id == Message.sender_id,
                ),
            )
        )
        .exists()
    )
    filters = [
        Message.recipient_id == recipient_id,
        Message.read_at.is_(None),
        blocked_pair,
    ]
    if sender_id is not None:
        filters.append(Message.sender_id == sender_id)
    return int(db.scalar(select(func.count(Message.id)).where(*filters)) or 0)


def unread_counts(db: Session, user_id: str) -> tuple[int, int]:
    notifications = int(
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.recipient_id == user_id,
                Notification.read_at.is_(None),
            )
        )
        or 0
    )
    return notifications, unread_message_count(db, user_id)


def profile(
    db: Session, user: User, viewer: User | None = None, public: bool = False
) -> dict[str, Any]:
    followers = int(
        db.scalar(
            select(func.count())
            .select_from(Follow)
            .where(Follow.followed_id == user.id)
        )
        or 0
    )
    following = int(
        db.scalar(
            select(func.count())
            .select_from(Follow)
            .where(Follow.follower_id == user.id)
        )
        or 0
    )
    result = {
        **lite(user),
        "instagram": user.instagram,
        "snapchat": user.snapchat,
        "twitter": user.twitter,
        "social_links": {
            "instagram": (
                f"https://www.instagram.com/{user.instagram}/" if user.instagram else ""
            ),
            "snapchat": (
                f"https://www.snapchat.com/add/{user.snapchat}" if user.snapchat else ""
            ),
            "twitter": f"https://x.com/{user.twitter}" if user.twitter else "",
        },
        "followers": followers,
        "following": following,
        "is_following": bool(viewer and db.get(Follow, (viewer.id, user.id))),
        "follows_you": bool(viewer and db.get(Follow, (user.id, viewer.id))),
        "blocked_by_you": bool(viewer and db.get(Block, (viewer.id, user.id))),
        "is_blocked": bool(viewer and is_blocked(db, viewer.id, user.id)),
        "stats": stats(db, user.id),
    }
    if not public:
        result.update(
            role=user.role,
            bot={
                "name": user.bot_name,
                "avatar_url": (
                    f"/media/{user.bot_avatar_id}" if user.bot_avatar_id else None
                ),
            },
        )
    return result


def add_notification(
    db: Session,
    recipient: str,
    actor: str | None,
    kind: str,
    body: str,
    resource: str = "",
):
    db.add(
        Notification(
            recipient_id=recipient,
            actor_id=actor,
            kind=kind,
            body=body[:240],
            resource=resource[:100],
        )
    )


def set_avatar(db: Session, user: User, data: bytes, kind: str):
    try:
        image = normalized_avatar(data)
    except ValueError as exc:
        fail(422, "invalid_avatar", str(exc))
    old_id = user.avatar_id if kind == "avatar" else user.bot_avatar_id
    media = Media(
        id=uid(),
        user_id=user.id,
        kind=kind,
        data=image,
        etag=hashlib.sha256(image).hexdigest(),
    )
    db.add(media)
    if kind == "avatar":
        user.avatar_id = media.id
    else:
        user.bot_avatar_id = media.id
    db.flush()
    if old_id:
        old = db.get(Media, old_id)
        if old:
            db.delete(old)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = make_engine(settings.database_url)
    factory = make_session_factory(engine)
    limiter = RateLimiter()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(engine)
        if settings.admin_username and settings.admin_password:
            try:
                username = normalize_username(settings.admin_username)
                validate_password(settings.admin_password)
            except ValueError as exc:
                raise RuntimeError(
                    f"Invalid administrator bootstrap configuration: {exc}"
                ) from exc
            with factory() as db:
                user = db.scalar(select(User).where(User.username == username))
                if user is None:
                    user = User(
                        username=username,
                        display_name=username,
                        password_hash=password_hash(settings.admin_password),
                        role="admin",
                    )
                    db.add(user)
                    try:
                        db.commit()
                    except IntegrityError:
                        db.rollback()
                # Existing accounts are never promoted or have their credentials changed.
        yield
        engine.dispose()

    app = FastAPI(lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.settings = settings
    app.state.limiter = limiter

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'",
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def rate_limit(
        request: Request, category: str, limit: int, identity: str | None = None
    ):
        if settings.testing:
            return
        limiter.check(
            f"{category}:ip:{request.client.host if request.client else 'unknown'}",
            limit,
            60,
        )
        if identity:
            limiter.check(f"{category}:{identity}", limit, 60)

    def authenticated(request: Request, db: Session):
        user, sess = require_user(request, db)
        return user, sess

    def challenge_payload(
        db: Session, challenge: Challenge, viewer: User, token: str | None = None
    ) -> dict[str, Any]:
        now = utcnow()
        if challenge.status == "lobby" and aware(challenge.expires_at) <= now:
            challenge.status = "expired"
            db.flush()
        members = db.scalars(
            select(ChallengeParticipant).where(
                ChallengeParticipant.challenge_id == challenge.id
            )
        ).all()
        round_ids = [m.round_id for m in members if m.round_id]
        completed = [m for m in members if m.finished_at]
        if challenge.status == "active" and (
            len(completed) == len(members)
            or (challenge.deadline_at and aware(challenge.deadline_at) <= now)
        ):
            challenge.status = "complete"
            db.flush()
        is_member = any(m.user_id == viewer.id for m in members)
        parts = []
        candidates = []
        for member in members:
            u = db.get(User, member.user_id)
            attempt = db.get(Attempt, member.attempt_id) if member.attempt_id else None
            item = {"user": lite(u), "finished": bool(member.finished_at)}
            if attempt:
                item["result"] = {
                    "wpm": attempt.wpm,
                    "accuracy": attempt.accuracy,
                    "points": attempt.points,
                }
                if attempt.eligible:
                    candidates.append(
                        (attempt.wpm, attempt.accuracy, attempt.points, u)
                    )
            parts.append(item)
        winner = (
            max(candidates, key=lambda x: (x[0], x[1], x[2]))[3]
            if candidates and challenge.status == "complete"
            else None
        )
        round_obj = None
        if is_member and challenge.status in {"active", "complete"}:
            own = next((m for m in members if m.user_id == viewer.id), None)
            r = db.get(PracticeRound, own.round_id) if own and own.round_id else None
            if r:
                round_obj = {
                    "id": r.id,
                    "target": r.expected,
                    "display": r.display,
                    "game": r.game,
                    "difficulty": r.difficulty,
                    "language": r.language,
                    "word_count": r.word_count,
                    "starts_at": iso(challenge.starts_at),
                    "challenge_id": challenge.id,
                }
        data = {
            "id": challenge.id,
            "owner": lite(db.get(User, challenge.owner_id)),
            "visibility": challenge.visibility,
            "status": challenge.status,
            "game": challenge.game,
            "difficulty": challenge.difficulty,
            "language": challenge.language,
            "max_players": challenge.max_players,
            "created_at": iso(challenge.created_at),
            "starts_at": iso(challenge.starts_at),
            "deadline_at": iso(challenge.deadline_at),
            "participants": parts,
            "round": round_obj,
            "winner": lite(winner) if winner else None,
            "server_now": iso(now),
        }
        if token is not None or challenge.visibility == "public":
            data["token"] = token or challenge.invite_token
        return data

    @app.get("/healthz")
    def health(db: Session = Depends(db_session)):
        try:
            db.execute(select(1))
            return {"status": "ok", "database": "ok"}
        except Exception:
            return Response(
                content='{"status":"error","database":"error"}',
                status_code=503,
                media_type="application/json",
            )

    @app.get("/")
    def index():
        path = Path(__file__).resolve().parent.parent / "static" / "index.html"
        if path.is_file():
            return FileResponse(path)
        raise HTTPException(404, "index.html not found")

    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/media/{media_id}")
    def media_get(media_id: str, request: Request, db: Session = Depends(db_session)):
        media = db.get(Media, media_id)
        if not media or media.kind not in {"avatar", "bot"}:
            raise HTTPException(404, "Media not found")
        headers = {
            "ETag": f'"{media.etag}"',
            "Cache-Control": "public, max-age=86400, immutable",
            "X-Content-Type-Options": "nosniff",
        }
        if request.headers.get("if-none-match", "").strip('"') == media.etag:
            return Response(status_code=304, headers=headers)
        return Response(media.data, media_type="image/webp", headers=headers)

    @app.get("/api/session")
    def session_info(request: Request, db: Session = Depends(db_session)):
        user, sess = get_session_user(request, db)
        if not user:
            return {
                "user": None,
                "csrf": None,
                "unread_notifications": 0,
                "unread_messages": 0,
            }
        notifications, messages = unread_counts(db, user.id)
        return {
            "user": profile(db, user),
            "csrf": sess.csrf_token,
            "unread_notifications": int(notifications),
            "unread_messages": int(messages),
        }

    def issue_session(response: Response, user: User, db: Session):
        db.execute(
            delete(LoginSession).where(
                LoginSession.user_id == user.id, LoginSession.expires_at <= utcnow()
            )
        )
        old_sessions = db.scalars(
            select(LoginSession)
            .where(LoginSession.user_id == user.id)
            .order_by(desc(LoginSession.created_at))
            .offset(9)
        ).all()
        for old_session in old_sessions:
            db.delete(old_session)
        token, csrf = opaque_token(), opaque_token()
        row = LoginSession(
            token_hash=digest_token(token),
            user_id=user.id,
            csrf_token=csrf,
            expires_at=utcnow() + timedelta(days=settings.session_days),
        )
        db.add(row)
        db.commit()
        response.set_cookie(
            "mt_session",
            token,
            max_age=settings.session_days * 86400,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
        )
        notifications, messages = unread_counts(db, user.id)
        return {
            "user": profile(db, user),
            "csrf": csrf,
            "unread_notifications": notifications,
            "unread_messages": messages,
        }

    @app.post("/api/auth/register")
    def register(
        payload: Credentials,
        request: Request,
        response: Response,
        db: Session = Depends(db_session),
    ):
        same_origin(request)
        rate_limit(request, "register", 8)
        try:
            username = normalize_username(payload.username)
            pw = validate_password(payload.password)
            display = clean_text(payload.display_name or username, 1, 40)
        except ValueError as exc:
            fail(422, "invalid_input", str(exc))
        if settings.admin_username:
            try:
                reserved = normalize_username(settings.admin_username)
            except ValueError:
                reserved = settings.admin_username.lower()
            if username == reserved:
                fail(409, "reserved_username", "This username is reserved.")
        user = User(
            username=username,
            display_name=display,
            password_hash=password_hash(pw),
            role="user",
        )
        db.add(user)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            fail(409, "username_taken", "Username is already registered.")
        return issue_session(response, user, db)

    @app.post("/api/auth/login")
    def login(
        payload: Credentials,
        request: Request,
        response: Response,
        db: Session = Depends(db_session),
    ):
        same_origin(request)
        candidate_name = payload.username.strip().lower()
        rate_limit(request, "login", 12, f"user:{candidate_name}")
        try:
            username = normalize_username(payload.username)
        except ValueError:
            username = payload.username.strip().lower()
        user = db.scalar(select(User).where(User.username == username))
        if not user or not password_matches(user.password_hash, payload.password):
            fail(401, "invalid_credentials", "Invalid username or password.")
        return issue_session(response, user, db)

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response, db: Session = Depends(db_session)):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        db.delete(sess)
        db.commit()
        response.delete_cookie(
            "mt_session",
            path="/",
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
        )
        return {"ok": True}

    @app.get("/api/me")
    def me(request: Request, db: Session = Depends(db_session)):
        user, _ = authenticated(request, db)
        return {"user": profile(db, user)}

    @app.patch("/api/me/profile")
    def patch_profile(
        payload: ProfileInput, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        try:
            user.display_name = clean_text(payload.display_name, 1, 40)
            user.instagram = social_handle(payload.instagram, "instagram")
            user.snapchat = social_handle(payload.snapchat, "snapchat")
            user.twitter = social_handle(payload.twitter, "twitter")
        except ValueError as exc:
            fail(422, "invalid_profile", str(exc))
        db.commit()
        return {"user": profile(db, user)}

    async def upload_avatar(
        request: Request, image: UploadFile, kind: str, db: Session
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        data = await image.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            fail(422, "invalid_avatar", "Upload must be no larger than 2 MB.")
        set_avatar(db, user, data, kind)
        db.commit()
        return {"user": profile(db, user)}

    @app.post("/api/me/avatar")
    async def avatar(
        request: Request,
        image: UploadFile = File(...),
        db: Session = Depends(db_session),
    ):
        return await upload_avatar(request, image, "avatar", db)

    @app.patch("/api/me/bot")
    def patch_bot(
        payload: BotInput, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        try:
            user.bot_name = clean_text(payload.name, 1, 40)
        except ValueError as exc:
            fail(422, "invalid_bot", str(exc))
        db.commit()
        return {"user": profile(db, user)}

    @app.post("/api/me/bot/avatar")
    async def bot_avatar(
        request: Request,
        image: UploadFile = File(...),
        db: Session = Depends(db_session),
    ):
        return await upload_avatar(request, image, "bot", db)

    @app.get("/api/users/search")
    def search_users(q: str = "", db: Session = Depends(db_session)):
        term = q.strip().lower()[:24]
        rows = (
            db.scalars(
                select(User)
                .where(User.username.contains(term, autoescape=True))
                .order_by(User.username)
                .limit(20)
            ).all()
            if term
            else []
        )
        return {"users": [lite(u) for u in rows]}

    def target_user(username: str, db: Session):
        try:
            name = normalize_username(username)
        except ValueError:
            raise HTTPException(404, "User not found")
        user = db.scalar(select(User).where(User.username == name))
        if not user:
            raise HTTPException(404, "User not found")
        return user

    @app.get("/api/users/{username}")
    def public_user(username: str, request: Request, db: Session = Depends(db_session)):
        target = target_user(username, db)
        viewer, _ = get_session_user(request, db)
        return {"user": profile(db, target, viewer, public=True)}

    @app.post("/api/users/{username}/follow")
    def follow(username: str, request: Request, db: Session = Depends(db_session)):
        actor, sess = authenticated(request, db)
        mutation_guard(request, actor, sess)
        target = target_user(username, db)
        lock_user_pair(db, actor.id, target.id)
        if target.id == actor.id or is_blocked(db, actor.id, target.id):
            fail(403, "follow_forbidden", "Following is not allowed.")
        if not db.get(Follow, (actor.id, target.id)):
            db.add(Follow(follower_id=actor.id, followed_id=target.id))
            add_notification(db, target.id, actor.id, "follow", "بدأ بمتابعتك")
        db.commit()
        return {"user": profile(db, target, actor, public=True)}

    @app.delete("/api/users/{username}/follow")
    def unfollow(username: str, request: Request, db: Session = Depends(db_session)):
        actor, sess = authenticated(request, db)
        mutation_guard(request, actor, sess)
        target = target_user(username, db)
        lock_user_pair(db, actor.id, target.id)
        row = db.get(Follow, (actor.id, target.id))
        if row:
            db.delete(row)
            db.commit()
        return {"user": profile(db, target, actor, public=True)}

    @app.get("/api/me/following")
    def following(request: Request, db: Session = Depends(db_session)):
        actor, _ = authenticated(request, db)
        rows = db.scalars(
            select(User)
            .join(Follow, Follow.followed_id == User.id)
            .where(Follow.follower_id == actor.id)
            .order_by(User.username)
        ).all()
        return {"users": [lite(u) for u in rows]}

    @app.post("/api/users/{username}/block")
    def block(username: str, request: Request, db: Session = Depends(db_session)):
        actor, sess = authenticated(request, db)
        mutation_guard(request, actor, sess)
        target = target_user(username, db)
        lock_user_pair(db, actor.id, target.id)
        if target.id == actor.id:
            fail(400, "self_block", "You cannot block yourself.")
        if not db.get(Block, (actor.id, target.id)):
            db.add(Block(blocker_id=actor.id, blocked_id=target.id))
        for pair in ((actor.id, target.id), (target.id, actor.id)):
            f = db.get(Follow, pair)
            if f:
                db.delete(f)
        db.commit()
        return {"ok": True}

    @app.delete("/api/users/{username}/block")
    def unblock(username: str, request: Request, db: Session = Depends(db_session)):
        actor, sess = authenticated(request, db)
        mutation_guard(request, actor, sess)
        target = target_user(username, db)
        lock_user_pair(db, actor.id, target.id)
        row = db.get(Block, (actor.id, target.id))
        if row:
            db.delete(row)
            db.commit()
        return {"ok": True}

    @app.get("/api/leaderboard")
    def leaderboard(sort: str = "points", db: Session = Depends(db_session)):
        if sort not in {"points", "wpm"}:
            fail(422, "invalid_sort", "sort must be points or wpm")
        metric = func.sum(Attempt.points) if sort == "points" else func.max(Attempt.wpm)
        ids = db.execute(
            select(Attempt.user_id, metric.label("metric"))
            .where(Attempt.eligible.is_(True))
            .group_by(Attempt.user_id)
            .order_by(desc("metric"))
            .limit(30)
        ).all()
        users = [db.get(User, item[0]) for item in ids]
        return {"users": [profile(db, u, public=True) for u in users if u]}

    @app.get("/api/messages/threads")
    def threads(request: Request, db: Session = Depends(db_session)):
        actor, _ = authenticated(request, db)
        rows = db.scalars(
            select(Message)
            .where(or_(Message.sender_id == actor.id, Message.recipient_id == actor.id))
            .order_by(desc(Message.id))
        ).all()
        latest = {}
        for m in rows:
            other = m.recipient_id if m.sender_id == actor.id else m.sender_id
            if other not in latest and not is_blocked(db, actor.id, other):
                latest[other] = m
        out = []
        for other, m in latest.items():
            unread = unread_message_count(db, actor.id, other)
            out.append(
                {
                    "user": lite(db.get(User, other)),
                    "last_message": {
                        "id": m.id,
                        "body": m.body,
                        "created_at": iso(m.created_at),
                        "sender_id": m.sender_id,
                    },
                    "unread": unread,
                }
            )
        out.sort(key=lambda x: x["last_message"]["id"], reverse=True)
        return {"threads": out}

    @app.get("/api/messages/{username}")
    def messages(
        username: str,
        request: Request,
        after: int = 0,
        db: Session = Depends(db_session),
    ):
        actor, _ = authenticated(request, db)
        other = target_user(username, db)
        if is_blocked(db, actor.id, other.id):
            fail(403, "blocked", "Messaging is unavailable.")
        rows = db.scalars(
            select(Message)
            .where(
                Message.id > max(0, after),
                or_(
                    and_(
                        Message.sender_id == actor.id, Message.recipient_id == other.id
                    ),
                    and_(
                        Message.sender_id == other.id, Message.recipient_id == actor.id
                    ),
                ),
            )
            .order_by(Message.id)
            .limit(100)
        ).all()
        return {
            "user": lite(other),
            "messages": [
                {
                    "id": m.id,
                    "sender_id": m.sender_id,
                    "recipient_id": m.recipient_id,
                    "body": m.body,
                    "created_at": iso(m.created_at),
                }
                for m in rows
            ],
        }

    @app.post("/api/messages/{username}")
    def send_message(
        username: str,
        payload: MessageInput,
        request: Request,
        db: Session = Depends(db_session),
    ):
        actor, sess = authenticated(request, db)
        mutation_guard(request, actor, sess)
        other = target_user(username, db)
        lock_user_pair(db, actor.id, other.id)
        if actor.id == other.id or is_blocked(db, actor.id, other.id):
            fail(403, "message_forbidden", "Messaging is not allowed.")
        try:
            body = clean_text(payload.body, 1, 2000)
        except ValueError as exc:
            fail(422, "invalid_message", str(exc))
        m = Message(sender_id=actor.id, recipient_id=other.id, body=body)
        db.add(m)
        db.flush()
        add_notification(
            db,
            other.id,
            actor.id,
            "message",
            "لديك رسالة جديدة",
            f"/messages/{actor.username}",
        )
        db.commit()
        return {
            "message": {
                "id": m.id,
                "sender_id": m.sender_id,
                "recipient_id": m.recipient_id,
                "body": m.body,
                "created_at": iso(m.created_at),
            }
        }

    @app.post("/api/messages/{username}/read")
    def read_messages(
        username: str, request: Request, db: Session = Depends(db_session)
    ):
        actor, sess = authenticated(request, db)
        mutation_guard(request, actor, sess)
        other = target_user(username, db)
        if is_blocked(db, actor.id, other.id):
            fail(403, "blocked", "Messaging is unavailable.")
        db.execute(
            update(Message)
            .where(
                Message.sender_id == other.id,
                Message.recipient_id == actor.id,
                Message.read_at.is_(None),
            )
            .values(read_at=utcnow())
        )
        db.commit()
        return {"ok": True}

    @app.get("/api/notifications")
    def notifications(request: Request, db: Session = Depends(db_session)):
        actor, _ = authenticated(request, db)
        rows = db.scalars(
            select(Notification)
            .where(Notification.recipient_id == actor.id)
            .order_by(desc(Notification.id))
            .limit(100)
        ).all()
        unread = int(
            db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.recipient_id == actor.id,
                    Notification.read_at.is_(None),
                )
            )
            or 0
        )
        return {
            "notifications": [
                {
                    "id": n.id,
                    "kind": n.kind,
                    "body": n.body,
                    "resource": n.resource,
                    "actor": (
                        lite(db.get(User, n.actor_id))
                        if n.actor_id and db.get(User, n.actor_id)
                        else None
                    ),
                    "created_at": iso(n.created_at),
                    "read": n.read_at is not None,
                }
                for n in rows
            ],
            "unread": unread,
        }

    @app.post("/api/notifications/read")
    def read_notifications(
        payload: ReadInput, request: Request, db: Session = Depends(db_session)
    ):
        actor, sess = authenticated(request, db)
        mutation_guard(request, actor, sess)
        stmt = update(Notification).where(
            Notification.recipient_id == actor.id, Notification.read_at.is_(None)
        )
        if payload.ids:
            stmt = stmt.where(Notification.id.in_(payload.ids))
        db.execute(stmt.values(read_at=utcnow()))
        db.commit()
        return {"ok": True}

    def new_round(
        user: User,
        payload: RoundInput,
        db: Session,
        challenge_id: str | None = None,
        generated=None,
        started_at=None,
    ):
        try:
            target = generated or generate_target(
                payload.game, payload.difficulty, payload.language, payload.count
            )
        except (ValueError, RuntimeError) as exc:
            fail(422, "invalid_round", str(exc))
        round_obj = PracticeRound(
            id=uid(),
            user_id=user.id,
            expected=target.target,
            display=target.display,
            game=target.game,
            difficulty=target.difficulty,
            language=target.language,
            word_count=target.word_count,
            challenge_id=challenge_id,
            started_at=started_at,
        )
        db.add(round_obj)
        db.flush()
        return round_obj

    @app.post("/api/rounds")
    def create_round(
        payload: RoundInput, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        # Avoid repeats of the complete expected text from the latest 20 rounds.
        recent = set(
            db.scalars(
                select(PracticeRound.expected)
                .where(PracticeRound.user_id == user.id)
                .order_by(desc(PracticeRound.created_at))
                .limit(20)
            ).all()
        )
        target = None
        for _ in range(8):
            try:
                candidate = generate_target(
                    payload.game, payload.difficulty, payload.language, payload.count
                )
            except (ValueError, RuntimeError) as exc:
                fail(422, "invalid_round", str(exc))
            if candidate.target not in recent:
                target = candidate
                break
        if target is None:
            target = candidate
        r = new_round(user, payload, db, generated=target)
        db.commit()
        return {
            "round": {
                "id": r.id,
                "target": r.expected,
                "display": r.display,
                "game": r.game,
                "difficulty": r.difficulty,
                "language": r.language,
                "word_count": r.word_count,
                "starts_at": None,
                "challenge_id": None,
            }
        }

    def owned_round(round_id: str, user: User, db: Session, lock: bool = False):
        query = select(PracticeRound).where(
            PracticeRound.id == round_id, PracticeRound.user_id == user.id
        )
        if lock:
            query = query.with_for_update()
        r = db.scalar(query)
        if not r:
            raise HTTPException(404, "Round not found")
        return r

    @app.post("/api/rounds/{round_id}/begin")
    def begin_round(round_id: str, request: Request, db: Session = Depends(db_session)):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        r = owned_round(round_id, user, db, True)
        if r.cancelled or r.submitted_at:
            fail(409, "round_closed", "This round is already closed.")
        if r.started_at is None and r.challenge_id is None:
            r.started_at = utcnow()
        db.commit()
        return {"started_at": iso(r.started_at)}

    def submit_round(
        round_id: str,
        payload: SubmitInput,
        user: User,
        db: Session,
        req: Request,
        sess: LoginSession,
        challenge: Challenge | None = None,
    ):
        mutation_guard(req, user, sess)
        r = owned_round(round_id, user, db, True)
        if r.cancelled or r.submitted_at:
            fail(409, "round_closed", "This round is already submitted or cancelled.")
        now = utcnow()
        start = aware(r.started_at or r.created_at)
        if challenge:
            if (
                challenge.status != "active"
                or not challenge.starts_at
                or not challenge.deadline_at
                or now < aware(challenge.starts_at)
                or now > aware(challenge.deadline_at)
            ):
                fail(
                    409,
                    "challenge_not_active",
                    "Challenge is not accepting submissions.",
                )
            start = aware(challenge.starts_at)
        elapsed = max(0.001, (now - start).total_seconds())
        try:
            result = score_attempt(r.expected, payload.text, elapsed)
        except ValueError as exc:
            fail(422, "invalid_attempt", str(exc))
        eligible = elapsed >= 1 and result["wpm"] <= 300
        result["eligible"] = eligible
        if challenge and not eligible:
            # Keep a truthful ineligible result but do not qualify it for the winner.
            pass
        attempt = Attempt(
            round_id=r.id,
            user_id=user.id,
            game=r.game,
            difficulty=r.difficulty,
            language=r.language,
            points=result["points"],
            penalty=result["penalty"],
            accuracy=result["accuracy"],
            wpm=result["wpm"],
            elapsed_seconds=elapsed,
            correct_characters=result["correct_characters"],
            error_count=result["error_count"],
            eligible=eligible,
        )
        db.add(attempt)
        r.submitted_at = now
        try:
            db.flush()
            if challenge:
                part = db.get(ChallengeParticipant, (challenge.id, user.id))
                part.attempt_id = attempt.id
                part.finished_at = now
            db.commit()
        except IntegrityError:
            db.rollback()
            fail(409, "round_closed", "This round has already been submitted.")
        result["stats"] = stats(db, user.id)
        return {"result": result, "stats": result["stats"]}

    @app.post("/api/rounds/{round_id}/submit")
    def submit(
        round_id: str,
        payload: SubmitInput,
        request: Request,
        db: Session = Depends(db_session),
    ):
        user, sess = authenticated(request, db)
        r = owned_round(round_id, user, db, True)
        if r.challenge_id:
            challenge = db.scalar(
                select(Challenge)
                .where(Challenge.id == r.challenge_id)
                .with_for_update()
            )
            part = (
                db.get(ChallengeParticipant, (challenge.id, user.id))
                if challenge
                else None
            )
            if not challenge or not part or part.round_id != r.id:
                fail(403, "round_forbidden", "Round is not yours.")
            return submit_round(round_id, payload, user, db, request, sess, challenge)
        return submit_round(round_id, payload, user, db, request, sess)

    @app.post("/api/rounds/{round_id}/cancel")
    def cancel_round(
        round_id: str, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        r = owned_round(round_id, user, db, True)
        if r.submitted_at:
            fail(409, "round_closed", "Submitted rounds cannot be cancelled.")
        r.cancelled = True
        db.commit()
        return {"ok": True}

    @app.get("/api/attempts")
    def attempts(request: Request, db: Session = Depends(db_session)):
        user, _ = authenticated(request, db)
        rows = db.scalars(
            select(Attempt)
            .where(Attempt.user_id == user.id)
            .order_by(desc(Attempt.created_at))
            .limit(20)
        ).all()
        return {
            "attempts": [
                {
                    "id": a.id,
                    "round_id": a.round_id,
                    "game": a.game,
                    "difficulty": a.difficulty,
                    "language": a.language,
                    "points": a.points,
                    "accuracy": a.accuracy,
                    "wpm": a.wpm,
                    "elapsed_seconds": a.elapsed_seconds,
                    "eligible": a.eligible,
                    "created_at": iso(a.created_at),
                }
                for a in rows
            ]
        }

    def find_challenge(token: str, db: Session, lock: bool = False):
        query = select(Challenge).where(Challenge.invite_token == token)
        if lock:
            query = query.with_for_update()
        c = db.scalar(query)
        if not c:
            raise HTTPException(404, "Challenge not found")
        return c

    @app.get("/api/challenges")
    def challenges(request: Request, db: Session = Depends(db_session)):
        user, _ = authenticated(request, db)
        rows = db.scalars(
            select(Challenge)
            .where(
                Challenge.visibility == "public",
                Challenge.status == "lobby",
                Challenge.expires_at > utcnow(),
            )
            .order_by(desc(Challenge.created_at))
            .limit(50)
        ).all()
        return {"challenges": [challenge_payload(db, c, user) for c in rows]}

    @app.post("/api/challenges")
    def create_challenge(
        payload: ChallengeInput, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        if payload.visibility not in {"private", "public"}:
            fail(422, "invalid_visibility", "visibility must be private or public")
        if (
            payload.game not in {"sentences", "stories", "news", "repeat"}
            or payload.difficulty not in {"easy", "medium", "hard"}
            or payload.language not in {"ar", "en"}
        ):
            fail(422, "invalid_challenge", "Invalid game, difficulty, or language.")
        if (payload.game == "repeat") != (payload.count is not None):
            fail(
                422,
                "invalid_challenge",
                "Repeat challenges require count; other games do not use count.",
            )
        now = utcnow()
        token = opaque_token()
        c = Challenge(
            id=uid(),
            invite_token=token,
            owner_id=user.id,
            visibility=payload.visibility,
            game=payload.game,
            difficulty=payload.difficulty,
            language=payload.language,
            word_count=payload.count,
            max_players=payload.max_players,
            status="lobby",
            target="",
            display="",
            created_at=now,
            expires_at=now + timedelta(hours=24),
        )
        db.add(c)
        db.flush()
        db.add(ChallengeParticipant(challenge_id=c.id, user_id=user.id))
        db.commit()
        return {"challenge": challenge_payload(db, c, user, token)}

    @app.get("/api/challenges/{token}")
    def get_challenge(token: str, request: Request, db: Session = Depends(db_session)):
        user, _ = authenticated(request, db)
        c = find_challenge(token, db, True)
        # Possession of the opaque invitation permits a lobby preview and join;
        # only members receive their target/round after the shared start.
        data = challenge_payload(db, c, user, token)
        db.commit()
        return {"challenge": data}

    @app.post("/api/challenges/{token}/join")
    def join_challenge(token: str, request: Request, db: Session = Depends(db_session)):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        c = find_challenge(token, db, True)
        if c.status == "lobby" and aware(c.expires_at) <= utcnow():
            c.status = "expired"
            db.commit()
        if c.status != "lobby":
            fail(409, "challenge_closed", "Challenge is no longer accepting players.")
        if is_blocked(db, user.id, c.owner_id):
            fail(403, "blocked", "Challenge join is unavailable.")
        members = db.scalars(
            select(ChallengeParticipant).where(
                ChallengeParticipant.challenge_id == c.id
            )
        ).all()
        if not db.get(ChallengeParticipant, (c.id, user.id)):
            if len(members) >= c.max_players:
                fail(409, "challenge_full", "Challenge is full.")
            db.add(ChallengeParticipant(challenge_id=c.id, user_id=user.id))
        db.commit()
        return {"challenge": challenge_payload(db, c, user, token)}

    @app.post("/api/challenges/{token}/start")
    def start_challenge(
        token: str, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        c = find_challenge(token, db, True)
        if c.owner_id != user.id:
            fail(403, "owner_only", "Only the challenge owner can start it.")
        if c.status == "lobby" and aware(c.expires_at) <= utcnow():
            c.status = "expired"
            db.commit()
        if c.status != "lobby":
            fail(409, "challenge_closed", "Challenge cannot be started.")
        members = db.scalars(
            select(ChallengeParticipant).where(
                ChallengeParticipant.challenge_id == c.id
            )
        ).all()
        if len(members) < 2:
            fail(409, "not_enough_players", "At least two players are required.")
        try:
            gen = generate_target(c.game, c.difficulty, c.language, c.word_count)
        except (ValueError, RuntimeError) as exc:
            fail(422, "invalid_challenge", str(exc))
        start = utcnow() + timedelta(seconds=3)
        c.target, c.display = gen.target, gen.display
        c.word_count, c.starts_at, c.deadline_at, c.status = (
            gen.word_count,
            start,
            start + timedelta(seconds=180),
            "active",
        )
        for part in members:
            p = RoundInput(
                game=c.game,
                difficulty=c.difficulty,
                language=c.language,
                count=c.word_count,
            )
            r = new_round(db.get(User, part.user_id), p, db, c.id, gen, start)
            part.round_id = r.id
        db.commit()
        return {"challenge": challenge_payload(db, c, user, token)}

    @app.post("/api/challenges/{token}/cancel")
    def cancel_challenge(
        token: str, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        c = find_challenge(token, db, True)
        if c.owner_id != user.id:
            fail(403, "owner_only", "Only the challenge owner can cancel it.")
        if c.status not in {"lobby", "active"}:
            fail(409, "challenge_closed", "Challenge is already closed.")
        c.status = "cancelled"
        db.commit()
        return {"ok": True, "challenge": challenge_payload(db, c, user, token)}

    @app.post("/api/suggestions")
    def suggest(
        payload: SuggestionInput, request: Request, db: Session = Depends(db_session)
    ):
        user, sess = authenticated(request, db)
        mutation_guard(request, user, sess)
        try:
            title = clean_text(payload.title, 1, 80)
            body = clean_text(payload.body, 1, 2000)
        except ValueError as exc:
            fail(422, "invalid_suggestion", str(exc))
        item = GameSuggestion(user_id=user.id, title=title, body=body)
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"suggestion": serialize_suggestion(item)}

    def serialize_suggestion(item: GameSuggestion, user: User | None = None):
        data = {
            "id": item.id,
            "title": item.title,
            "body": item.body,
            "status": item.status,
            "admin_note": item.admin_note,
            "created_at": iso(item.created_at),
            "reviewed_at": iso(item.reviewed_at),
        }
        if user:
            data["user"] = lite(user)
        return data

    @app.get("/api/suggestions/mine")
    def my_suggestions(request: Request, db: Session = Depends(db_session)):
        user, _ = authenticated(request, db)
        rows = db.scalars(
            select(GameSuggestion)
            .where(GameSuggestion.user_id == user.id)
            .order_by(desc(GameSuggestion.id))
        ).all()
        return {"suggestions": [serialize_suggestion(x) for x in rows]}

    def admin_user(request: Request, db: Session):
        user, sess = authenticated(request, db)
        if user.role != "admin":
            fail(403, "admin_required", "Administrator access required.")
        return user, sess

    @app.get("/api/admin/suggestions")
    def admin_suggestions(request: Request, db: Session = Depends(db_session)):
        admin_user(request, db)
        rows = db.scalars(
            select(GameSuggestion).order_by(GameSuggestion.status, GameSuggestion.id)
        ).all()
        return {
            "suggestions": [
                serialize_suggestion(x, db.get(User, x.user_id)) for x in rows
            ]
        }

    @app.patch("/api/admin/suggestions/{suggestion_id}")
    def review_suggestion(
        suggestion_id: int,
        payload: ReviewInput,
        request: Request,
        db: Session = Depends(db_session),
    ):
        admin, sess = admin_user(request, db)
        mutation_guard(request, admin, sess)
        if payload.status not in {"approved", "rejected"}:
            fail(422, "invalid_status", "status must be approved or rejected")
        item = db.get(GameSuggestion, suggestion_id)
        if not item:
            raise HTTPException(404, "Suggestion not found")
        item.status, item.admin_note, item.reviewed_by, item.reviewed_at = (
            payload.status,
            payload.admin_note.strip(),
            admin.id,
            utcnow(),
        )
        add_notification(
            db,
            item.user_id,
            admin.id,
            "suggestion_review",
            f"اقتراحك {('قُبل' if payload.status == 'approved' else 'رُفض')}",
            f"suggestion:{item.id}",
        )
        db.commit()
        return {"suggestion": serialize_suggestion(item)}

    return app
