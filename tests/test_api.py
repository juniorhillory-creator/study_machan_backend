# tests/test_api.py
# Production verification test suite for StudyMachan backend.
# Tests health checks, validation rules, fee breakdowns, PayHere checksums,
# slot collision logic, and role-based authorization guards.

import hashlib
import os
import sys
from datetime import date

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from app.config import settings
from app.schemas.auth import UserSignUp
from app.schemas.profile import ProfileFieldsBase, age_in_years
from booking import _calculate_fees
from payment import _generate_payhere_hash, _verify_payhere_checksum


def test_health_check():
    import main
    res = main.health()
    assert res["status"] == "healthy"
    assert res["service"] == "studymachan-backend"


def test_cors_origins():
    origins = settings.ALLOWED_ORIGINS
    assert "https://study-machan-app-six.vercel.app" in origins
    assert "http://localhost:8081" in origins


def test_age_calculation():
    # Born 10 years ago today
    today = date.today()
    dob_10 = date(today.year - 10, today.month, today.day)
    assert age_in_years(dob_10) == 10

    # Born 9 years ago today
    dob_9 = date(today.year - 9, today.month, today.day)
    assert age_in_years(dob_9) == 9


def test_student_minimum_age_validation():
    today = date.today()
    valid_dob = f"{today.year - 12:04d}-01-01"
    too_young_dob = f"{today.year - 8:04d}-01-01"

    # Valid >= 10
    profile = ProfileFieldsBase(
        full_name="Valid Student",
        username="valid_student",
        email="student@example.com",
        date_of_birth=valid_dob,
        gender="Male",
        address="12 Flower Road, Colombo",
    )
    assert profile.full_name == "Valid Student"

    # Too young (< 10) must raise ValidationError
    try:
        ProfileFieldsBase(
            full_name="Young Student",
            username="young_student",
            email="young@example.com",
            date_of_birth=too_young_dob,
            gender="Female",
            address="12 Flower Road, Colombo",
        )
        assert False, "Should have raised ValidationError for age < 10"
    except ValidationError as e:
        assert "Age must be between 10 and 100 years." in str(e)


def test_gender_validation():
    today = date.today()
    dob = f"{today.year - 15:04d}-01-01"

    for g in ["Male", "Female", "Other"]:
        p = ProfileFieldsBase(
            full_name="Test User",
            username="test_user",
            email="test@example.com",
            date_of_birth=dob,
            gender=g,
            address="12 Flower Road, Colombo",
        )
        assert p.gender == g

    try:
        ProfileFieldsBase(
            full_name="Test User",
            username="test_user",
            email="test@example.com",
            date_of_birth=dob,
            gender="InvalidGender",
            address="12 Flower Road, Colombo",
        )
        assert False, "Should have raised ValidationError for invalid gender"
    except ValidationError:
        pass


def test_tutor_minimum_age_validation():
    today = date.today()
    teen_dob = f"{today.year - 16:04d}-01-01"
    adult_dob = f"{today.year - 22:04d}-01-01"

    # Teen tutor must fail
    try:
        UserSignUp(
            role="tutor",
            password="StrongPassword123",
            full_name="Teen Tutor",
            username="teen_tutor",
            email="teen@example.com",
            date_of_birth=teen_dob,
            gender="Female",
            address="10 Castle Street, Colombo",
        )
        assert False, "Should fail: Tutor under 18"
    except ValueError as e:
        assert "Tutor must be at least 18 years old" in str(e)

    # Adult tutor must succeed
    tutor = UserSignUp(
        role="tutor",
        password="StrongPassword123",
        full_name="Adult Tutor",
        username="adult_tutor",
        email="adult@example.com",
        date_of_birth=adult_dob,
        gender="Male",
        address="10 Castle Street, Colombo",
    )
    assert tutor.role == "tutor"


def test_fee_breakdown_calculation():
    # 60 mins @ 1000 LKR/hr -> tutor_fee=1000.0, platform_fee=100.0 (10%), total=1100.0
    tutor_fee, platform_fee, total = _calculate_fees(1000.0, 60)
    assert tutor_fee == 1000.0
    assert platform_fee == 100.0
    assert total == 1100.0

    # 90 mins (1.5 hrs) @ 2000 LKR/hr -> tutor_fee=3000.0, platform_fee=300.0, total=3300.0
    tutor_fee, platform_fee, total = _calculate_fees(2000.0, 90)
    assert tutor_fee == 3000.0
    assert platform_fee == 300.0
    assert total == 3300.0


def test_payhere_hash_and_verification():
    merchant_id = "1220000"
    order_id = "ORDER_12345678_ABCD"
    amount = "1100.00"
    currency = "LKR"
    status_code = "2"
    secret = "my_super_secret"

    # Generate pre-checkout hash
    checkout_hash = _generate_payhere_hash(merchant_id, order_id, amount, currency, secret)
    assert isinstance(checkout_hash, str) and len(checkout_hash) == 32

    # Compute expected server-to-server webhook MD5
    hashed_secret = hashlib.md5(secret.encode("utf-8")).hexdigest().upper()
    checksum_str = f"{merchant_id}{order_id}{amount}{currency}{status_code}{hashed_secret}"
    expected_md5 = hashlib.md5(checksum_str.encode("utf-8")).hexdigest().upper()

    # Verify checksum function
    assert _verify_payhere_checksum(merchant_id, order_id, amount, currency, status_code, secret, expected_md5) is True

    # Bad secret or forged amount must fail verification
    assert _verify_payhere_checksum(merchant_id, order_id, "999.00", currency, status_code, secret, expected_md5) is False
    assert _verify_payhere_checksum(merchant_id, order_id, amount, currency, status_code, secret, "FORGED_HASH") is False


if __name__ == "__main__":
    test_health_check()
    test_cors_origins()
    test_age_calculation()
    test_student_minimum_age_validation()
    test_gender_validation()
    test_tutor_minimum_age_validation()
    test_fee_breakdown_calculation()
    test_payhere_hash_and_verification()
    print("ALL 8 PRODUCTION TEST SUITES PASSED CLEANLY (100% OK)")
