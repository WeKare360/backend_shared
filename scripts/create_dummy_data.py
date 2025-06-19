#!/usr/bin/env python3
"""
WeKare Dummy Data Creation Service
Creates realistic test data for all tables (20 rows each)
"""

import asyncio
import random
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from faker import Faker
import os

# Import all models
from wekare_profiles.database.models import Organization, User, Facility
from wekare_insurance.database.models import (
    CoverageVerification, Payer, VerificationStatus, PayerType, InsuranceType
)
from wekare_notifications.database.models import (
    Notification, NotificationType, NotificationStatus, NotificationPriority
)
from shared.database.base import Base

# Initialize Faker with medical provider
fake = Faker(['en_US', 'en_CA'])

class DummyDataService:
    """Service to create realistic dummy data for all WeKare tables"""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession)
        
        # Healthcare-specific data
        self.specialties = [
            "Cardiology", "Dermatology", "Endocrinology", "Gastroenterology",
            "Hematology", "Neurology", "Oncology", "Orthopedics", "Pediatrics",
            "Psychiatry", "Pulmonology", "Radiology", "Rheumatology", "Surgery",
            "Urology", "Ophthalmology", "ENT", "Pathology", "Anesthesiology", "Emergency Medicine"
        ]
        
        self.insurance_companies = [
            "Blue Cross Blue Shield", "UnitedHealth", "Kaiser Permanente", "Aetna",
            "Anthem", "Cigna", "Humana", "Molina Healthcare", "Centene", "Medicare",
            "Medicaid", "Tricare", "Aetna Better Health", "WellCare", "AmeriHealth",
            "Independence Blue Cross", "Oscar Health", "Bright Health", "Alignment Healthcare", "CareFirst"
        ]
        
        self.facility_types = [
            "hospital", "clinic", "urgent_care", "surgery_center", "imaging_center",
            "laboratory", "rehabilitation", "mental_health", "pediatric", "specialty_clinic"
        ]
        
        # Store created entities for relationships
        self.organizations = []
        self.users = []
        self.facilities = []
        self.payers = []
        self.coverage_verifications = []
        self.notifications = []

    async def create_all_dummy_data(self):
        """Create dummy data for all tables"""
        print("🎯 Starting WeKare Dummy Data Creation")
        print("=" * 60)
        
        async with self.async_session() as session:
            # Create data in dependency order
            await self.create_organizations(session, 20)
            await self.create_users(session, 20)
            await self.create_facilities(session, 20)
            await self.create_payers(session, 20)
            await self.create_coverage_verifications(session, 20)
            await self.create_notifications(session, 20)
            
            await session.commit()
            print("\n🎉 Dummy data creation completed successfully!")
            print(f"📊 Total records created:")
            print(f"   • Organizations: {len(self.organizations)}")
            print(f"   • Users: {len(self.users)}")
            print(f"   • Facilities: {len(self.facilities)}")
            print(f"   • Payers: {len(self.payers)}")
            print(f"   • Coverage Verifications: {len(self.coverage_verifications)}")
            print(f"   • Notifications: {len(self.notifications)}")

    async def create_organizations(self, session: AsyncSession, count: int):
        """Create dummy organizations"""
        print(f"🏢 Creating {count} organizations...")
        
        for i in range(count):
            org_name = f"{fake.company()} Medical Center"
            org = Organization(
                name=org_name,
                slug=f"{fake.slug()}-{i}",
                cognito_user_pool_id=f"us-east-1_{fake.uuid4().replace('-', '')[:25]}",
                cognito_client_id=fake.uuid4().replace('-', ''),
                cognito_domain_prefix=f"{fake.slug()}-{i}",
                region=random.choice(["us-east-1", "us-west-2", "us-east-2"]),
                settings={
                    "timezone": fake.timezone(),
                    "theme": random.choice(["light", "dark", "auto"]),
                    "notifications_enabled": True,
                    "max_users": random.randint(10, 500)
                },
                subscription_plan=random.choice(["free", "basic", "professional", "enterprise"])
            )
            session.add(org)
            await session.flush()
            self.organizations.append(org)

    async def create_users(self, session: AsyncSession, count: int):
        """Create dummy users"""
        print(f"👤 Creating {count} users...")
        
        for i in range(count):
            org = random.choice(self.organizations)
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@{org.slug}.com"
            
            user = User(
                organization_id=org.id,
                cognito_user_id=f"us-east-1:{fake.uuid4()}",
                cognito_username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                timezone=fake.timezone(),
                locale=random.choice(["en-US", "en-CA", "es-US", "fr-CA"]),
                preferences={
                    "dashboard_layout": random.choice(["grid", "list"]),
                    "email_frequency": random.choice(["immediate", "daily", "weekly"]),
                    "dark_mode": fake.boolean()
                },
                profile_settings={
                    "title": random.choice(["Dr.", "Nurse", "PA", "Administrator", "Coordinator"]),
                    "department": random.choice(["Emergency", "Cardiology", "Administration", "Nursing"]),
                    "phone": fake.phone_number()
                },
                notification_settings={
                    "email_notifications": True,
                    "sms_notifications": fake.boolean(),
                    "push_notifications": True
                }
            )
            session.add(user)
            await session.flush()
            self.users.append(user)

    async def create_facilities(self, session: AsyncSession, count: int):
        """Create dummy facilities"""
        print(f"🏥 Creating {count} facilities...")
        
        for i in range(count):
            org = random.choice(self.organizations)
            facility = Facility(
                organization_id=org.id,
                name=f"{fake.company()} {random.choice(['Medical Center', 'Clinic', 'Hospital', 'Surgery Center'])}",
                facility_type=random.choice(self.facility_types),
                address_line1=fake.street_address(),
                address_line2=fake.secondary_address() if fake.boolean() else None,
                city=fake.city(),
                state=fake.state(),
                state_code=fake.state_abbr(),
                zip_code=fake.zipcode(),
                phone=fake.phone_number(),
                email=fake.email(),
                npi=fake.numerify('##########'),
                tax_id=fake.numerify('##-#######'),
                facility_id=f"FAC{fake.numerify('######')}",
                is_active=fake.boolean(chance_of_getting_true=90)
            )
            session.add(facility)
            await session.flush()
            self.facilities.append(facility)

    async def create_payers(self, session: AsyncSession, count: int):
        """Create dummy payers"""
        print(f"💳 Creating {count} payers...")
        
        for i, payer_name in enumerate(self.insurance_companies[:count]):
            payer = Payer(
                name=payer_name,
                payer_id=f"PAY{i+1:06d}",
                code=f"INS{i+1:03d}",
                payer_type=random.choice(list(PayerType)),
                insurance_type=random.choice(list(InsuranceType)),
                state=fake.state_abbr(),
                phone=fake.phone_number(),
                website=f"https://www.{payer_name.lower().replace(' ', '')}.com",
                eligibility_phone=fake.phone_number(),
                claims_phone=fake.phone_number(),
                is_active=fake.boolean(chance_of_getting_true=85),
                supports_realtime_verification=fake.boolean(chance_of_getting_true=60),
                availity_payer_id=f"AVAIL{fake.numerify('######')}",
                additional_metadata={
                    "region": fake.state(),
                    "tier": random.choice(["tier1", "tier2", "tier3"]),
                    "claim_types": ["medical", "dental", "vision"]
                }
            )
            session.add(payer)
            await session.flush()
            self.payers.append(payer)

    async def create_coverage_verifications(self, session: AsyncSession, count: int):
        """Create dummy coverage verifications"""
        print(f"🔍 Creating {count} coverage verifications...")
        
        for i in range(count):
            org = random.choice(self.organizations)
            created_by = random.choice([u for u in self.users if u.organization_id == org.id])
            payer = random.choice(self.payers)
            
            verification = CoverageVerification(
                organization_id=org.id,
                created_by_user_id=created_by.id,
                
                # Patient Information
                patient_first_name=fake.first_name(),
                patient_last_name=fake.last_name(),
                health_card_number=fake.numerify('#### #### ####'),
                
                # Insurance Details
                insurance_company=payer.name,
                policy_number=fake.numerify('POL########'),
                group_number=fake.numerify('GRP######'),
                member_id=fake.numerify('MBR########'),
                payer_name=payer.name,
                
                # Coverage Details
                verification_status=random.choice(list(VerificationStatus)),
                status_code=random.choice(["A1", "A2", "A3", "D1", "D2", "P1"]),
                coverage_start_date=fake.past_date(start_date='-365d'),
                coverage_end_date=fake.future_date(end_date='+365d'),
                eligibility_start_date=fake.past_date(start_date='-365d'),
                eligibility_end_date=fake.future_date(end_date='+365d'),
                copay_amount=Decimal(str(random.randint(10, 100))),
                deductible_amount=Decimal(str(random.randint(500, 5000))),
                
                # Verification Details
                verification_date=fake.past_datetime(start_date='-7d'),
                verification_notes=fake.text(max_nb_chars=300),
                notes=fake.text(max_nb_chars=200),
                
                # Processing
                is_processed=fake.boolean(chance_of_getting_true=70),
                processed_at=fake.past_datetime(start_date='-3d') if fake.boolean() else None,
                processing_notes=fake.text(max_nb_chars=150) if fake.boolean() else None
            )
            session.add(verification)
            await session.flush()
            self.coverage_verifications.append(verification)

    async def create_notifications(self, session: AsyncSession, count: int):
        """Create dummy notifications"""
        print(f"🔔 Creating {count} notifications...")
        
        for i in range(count):
            org = random.choice(self.organizations)
            user = random.choice([u for u in self.users if u.organization_id == org.id])
            coverage = random.choice(self.coverage_verifications) if fake.boolean() else None
            
            notification_type = random.choice(list(NotificationType))
            
            notification = Notification(
                organization_id=org.id,
                user_id=user.id,
                coverage_verification_id=coverage.id if coverage else None,
                notification_type=notification_type,
                status=random.choice(list(NotificationStatus)),
                priority=random.choice(list(NotificationPriority)),
                title=self._generate_notification_title(notification_type),
                message=self._generate_notification_message(notification_type),
                read_at=fake.past_datetime(start_date='-7d') if fake.boolean() else None,
                email_sent=fake.boolean(chance_of_getting_true=70),
                sms_sent=fake.boolean(chance_of_getting_true=30),
                email_sent_at=fake.past_datetime(start_date='-7d') if fake.boolean() else None,
                sms_sent_at=fake.past_datetime(start_date='-7d') if fake.boolean() else None,
                scheduled_for=fake.future_datetime(end_date='+7d') if fake.boolean() else None,
                sent_at=fake.past_datetime(start_date='-7d'),
                expires_at=fake.future_datetime(end_date='+30d') if fake.boolean() else None,
                additional_data={
                    "source": random.choice(["system", "user", "automation"]),
                    "action_required": fake.boolean()
                }
            )
            session.add(notification)
            await session.flush()
            self.notifications.append(notification)

    def _generate_notification_title(self, notification_type: NotificationType) -> str:
        """Generate realistic notification titles based on type"""
        titles = {
            NotificationType.referral_assigned: "New Referral Assigned",
            NotificationType.referral_completed: "Referral Completed",
            NotificationType.referral_updated: "Referral Status Updated",
            NotificationType.coverage_verified: "Insurance Coverage Verified",
            NotificationType.coverage_expired: "Insurance Coverage Expired",
            NotificationType.verification_complete: "Verification Process Complete",
            NotificationType.system_alert: "System Alert",
            NotificationType.appointment_reminder: "Appointment Reminder",
            NotificationType.document_required: "Document Required",
            NotificationType.payment_due: "Payment Due"
        }
        return titles.get(notification_type, "System Notification")

    def _generate_notification_message(self, notification_type: NotificationType) -> str:
        """Generate realistic notification messages based on type"""
        messages = {
            NotificationType.referral_assigned: "A new referral has been assigned to you for review and processing.",
            NotificationType.referral_completed: "The referral process has been completed successfully.",
            NotificationType.referral_updated: "The referral status has been updated. Please review the changes.",
            NotificationType.coverage_verified: "Insurance coverage has been successfully verified for the patient.",
            NotificationType.coverage_expired: "Patient's insurance coverage has expired. Please update information.",
            NotificationType.verification_complete: "The verification process has been completed for this referral.",
            NotificationType.system_alert: "Important system alert requiring your attention.",
            NotificationType.appointment_reminder: "You have an upcoming appointment scheduled.",
            NotificationType.document_required: "Additional documentation is required to process this referral.",
            NotificationType.payment_due: "Payment is due for services rendered."
        }
        return messages.get(notification_type, "System notification message.")

async def main():
    """Main function to create all dummy data"""
    # Load environment variables for database connection
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:getgoing@localhost:5432/wekare"
    )
    
    print("🚀 WeKare Dummy Data Creation Service")
    print("=" * 60)
    print(f"📊 Database: {database_url.split('@')[-1] if '@' in database_url else 'local'}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    service = DummyDataService(database_url)
    
    try:
        await service.create_all_dummy_data()
    except Exception as e:
        print(f"❌ Error creating dummy data: {e}")
        raise
    finally:
        await service.engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 