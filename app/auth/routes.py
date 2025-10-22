from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.auth.models import User, OTPVerification, PasswordResetToken
from app.auth.schemas import (
    SignupRequest, VerifyOTPRequest, LoginRequest, 
    ForgotPasswordRequest, ResetPasswordRequest,
    TokenResponse, MessageResponse, UserProfile
)
from app.auth.utils import (
    hash_password, verify_password, generate_otp, generate_reset_token,
    create_jwt_token, decode_jwt_token, send_otp_email, send_password_reset_email
)
from app.core.config import settings

router = APIRouter()

@router.post("/signup", response_model=MessageResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user and send OTP for verification"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_pwd = hash_password(request.password)
    new_user = User(
        full_name=request.full_name,
        email=request.email,
        password_hash=hashed_pwd,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    
    # Generate and store OTP
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    # Delete any existing OTPs for this email
    db.query(OTPVerification).filter(OTPVerification.email == request.email).delete()
    
    otp_record = OTPVerification(
        email=request.email,
        otp=otp,
        expires_at=expiry
    )
    db.add(otp_record)
    db.commit()
    
    # Send OTP email
    send_otp_email(request.email, otp)
    
    return {"message": "OTP sent to your email for verification"}

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify email OTP and activate user account"""
    
    # Find OTP record
    otp_record = db.query(OTPVerification).filter(
        OTPVerification.email == request.email,
        OTPVerification.otp == request.otp
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Check expiry
    if datetime.utcnow() > otp_record.expires_at:
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )
    
    # Verify user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    db.delete(otp_record)
    db.commit()
    
    # Generate JWT token
    token = create_jwt_token(user.id, user.email)
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email first."
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    token = create_jwt_token(user.id, user.email)
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset link to user's email"""
    
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "Password reset link sent to your email"}
    
    # Generate reset token
    token = generate_reset_token()
    expiry = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRY_MINUTES)
    
    # Delete any existing tokens for this email
    db.query(PasswordResetToken).filter(
        PasswordResetToken.email == request.email
    ).delete()
    
    reset_token = PasswordResetToken(
        email=request.email,
        token=token,
        expires_at=expiry,
        used=False
    )
    db.add(reset_token)
    db.commit()
    
    # Send reset email
    send_password_reset_email(request.email, token)
    
    return {"message": "Password reset link sent to your email"}

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset user password using reset token"""
    
    # Find reset token
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.used == False
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check expiry
    if datetime.utcnow() > token_record.expires_at:
        db.delete(token_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Find user
    user = db.query(User).filter(User.email == token_record.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    token_record.used = True
    db.commit()
    
    return {"message": "Password reset successfully. Please log in again."}

@router.get("/user/profile", response_model=UserProfile)
def get_profile(authorization: str = Header(...), db: Session = Depends(get_db)):
    """Get current user profile (protected route)"""
    
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    # Decode token
    payload = decode_jwt_token(token)
    user_id = payload.get("user_id")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user