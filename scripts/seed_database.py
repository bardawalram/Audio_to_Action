"""
Database seeding script for ReATOA.
Creates test data: classes, sections, students, teachers, subjects, exam types,
accountant user, fee structures, and sample fee payments.
"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.authentication.models import CustomUser, Teacher
from apps.academics.models import Class, Section, ClassSection, Student
from apps.marks.models import Subject, ExamType
from apps.fees.models import FeeStructure, FeePayment
from faker import Faker

fake = Faker()


def create_classes():
    """Create Class records for grades 1-10"""
    print("Creating classes...")
    classes = []
    for grade in range(1, 11):
        class_obj, created = Class.objects.get_or_create(
            grade_number=grade,
            defaults={
                'name': f"{grade}th" if grade > 3 else f"{grade}st" if grade == 1 else f"{grade}nd" if grade == 2 else f"{grade}rd",
                'description': f"Grade {grade}"
            }
        )
        classes.append(class_obj)
        if created:
            print(f"  Created Class: {class_obj.name}")
    return classes


def create_sections():
    """Create Section records A, B, C"""
    print("Creating sections...")
    sections = []
    for section_name in ['A', 'B', 'C']:
        section, created = Section.objects.get_or_create(name=section_name)
        sections.append(section)
        if created:
            print(f"  Created Section: {section.name}")
    return sections


def create_class_sections(classes, sections):
    """Create ClassSection records for current academic year"""
    print("Creating class sections...")
    academic_year = "2024-2025"
    class_sections = []

    for class_obj in classes:
        for section in sections:
            class_section, created = ClassSection.objects.get_or_create(
                class_obj=class_obj,
                section=section,
                academic_year=academic_year,
                defaults={'max_students': 30}
            )
            class_sections.append(class_section)
            if created:
                print(f"  Created ClassSection: {class_section}")

    return class_sections


def create_students(class_sections):
    """Create 20 students for each class section"""
    print("Creating students...")
    genders = ['MALE', 'FEMALE']
    indian_first_names_male = [
        'Aarav', 'Vivaan', 'Aditya', 'Arjun', 'Sai', 'Arnav', 'Ayaan', 'Krishna',
        'Ishaan', 'Shaurya', 'Atharv', 'Advait', 'Pranav', 'Dhruv', 'Ansh'
    ]
    indian_first_names_female = [
        'Aadhya', 'Ananya', 'Pari', 'Anika', 'Angel', 'Diya', 'Isha', 'Kavya',
        'Anvi', 'Navya', 'Sara', 'Myra', 'Kiara', 'Saanvi', 'Avni'
    ]
    indian_last_names = [
        'Sharma', 'Kumar', 'Singh', 'Verma', 'Gupta', 'Patel', 'Reddy', 'Rao',
        'Agarwal', 'Joshi', 'Mehta', 'Desai', 'Nair', 'Iyer', 'Malhotra'
    ]

    student_count = 0
    for class_section in class_sections:
        for roll_num in range(1, 21):  # 20 students per class
            gender = random.choice(genders)
            if gender == 'MALE':
                first_name = random.choice(indian_first_names_male)
            else:
                first_name = random.choice(indian_first_names_female)

            last_name = random.choice(indian_last_names)

            # Generate date of birth based on class (approximate ages)
            age = 5 + class_section.class_obj.grade_number  # Grade 1 = 6 years old
            dob = date.today() - timedelta(days=age * 365 + random.randint(0, 365))

            student, created = Student.objects.get_or_create(
                roll_number=roll_num,
                class_section=class_section,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': dob,
                    'gender': gender,
                    'father_name': f"{random.choice(indian_first_names_male)} {last_name}",
                    'mother_name': f"{random.choice(indian_first_names_female)} {last_name}",
                    'phone_number': f"+91{random.randint(7000000000, 9999999999)}",
                    'is_active': True
                }
            )

            if created:
                student_count += 1

    print(f"  Created {student_count} students")


def create_subjects():
    """Create Subject records"""
    print("Creating subjects...")
    subjects_data = [
        {'name': 'Mathematics', 'code': 'MATH', 'max_marks': 100},
        {'name': 'Hindi', 'code': 'HINDI', 'max_marks': 100},
        {'name': 'English', 'code': 'ENGLISH', 'max_marks': 100},
        {'name': 'Science', 'code': 'SCIENCE', 'max_marks': 100},
        {'name': 'Social Studies', 'code': 'SOCIAL', 'max_marks': 100},
    ]

    subjects = []
    for subject_data in subjects_data:
        subject, created = Subject.objects.get_or_create(
            code=subject_data['code'],
            defaults={
                'name': subject_data['name'],
                'max_marks': subject_data['max_marks']
            }
        )
        subjects.append(subject)
        if created:
            print(f"  Created Subject: {subject.name}")

    return subjects


def create_exam_types():
    """Create ExamType records"""
    print("Creating exam types...")
    exam_types_data = [
        {'name': 'Unit Test', 'code': 'UNIT_TEST', 'weightage': 20.00},
        {'name': 'Midterm Exam', 'code': 'MIDTERM', 'weightage': 30.00},
        {'name': 'Final Exam', 'code': 'FINAL', 'weightage': 50.00},
    ]

    exam_types = []
    for exam_data in exam_types_data:
        exam_type, created = ExamType.objects.get_or_create(
            code=exam_data['code'],
            defaults={
                'name': exam_data['name'],
                'weightage': exam_data['weightage'],
                'is_active': True
            }
        )
        exam_types.append(exam_type)
        if created:
            print(f"  Created ExamType: {exam_type.name}")

    return exam_types


def create_teachers(subjects, class_sections):
    """Create teacher accounts"""
    print("Creating teachers...")
    teacher_count = 0

    # Create 5 teachers
    for i in range(1, 6):
        username = f"teacher{i}"

        # Create user
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'email': f"{username}@school.com",
                'role': CustomUser.Role.TEACHER,
                'is_active': True
            }
        )

        if created:
            user.set_password('password123')  # Default password
            user.save()

        # Create teacher profile
        teacher, teacher_created = Teacher.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': f"EMP{1000 + i}",
                'is_active': True
            }
        )

        if teacher_created:
            # Assign random subjects (2-3 subjects per teacher)
            teacher_subjects = random.sample(subjects, k=random.randint(2, 3))
            teacher.subjects.set(teacher_subjects)

            # Assign random classes (3-6 class sections per teacher)
            assigned_classes = random.sample(class_sections, k=random.randint(3, 6))
            teacher.assigned_classes.set(assigned_classes)

            teacher.save()
            teacher_count += 1
            print(f"  Created Teacher: {user.username} ({user.get_full_name()})")
            print(f"    Subjects: {', '.join([s.name for s in teacher_subjects])}")
            print(f"    Classes: {', '.join([str(c) for c in assigned_classes])}")

    print(f"  Total teachers created: {teacher_count}")
    print(f"  Default password for all teachers: password123")


def create_admin():
    """Create admin user"""
    print("Creating admin user...")
    admin, created = CustomUser.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@school.com',
            'role': CustomUser.Role.ADMIN,
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )

    if created:
        admin.set_password('admin123')
        admin.save()
        print(f"  Created admin user: admin / admin123")
    else:
        print(f"  Admin user already exists")


def create_accountant():
    """Create accountant user"""
    print("Creating accountant user...")
    accountant, created = CustomUser.objects.get_or_create(
        username='accountant1',
        defaults={
            'first_name': 'Rajesh',
            'last_name': 'Sharma',
            'email': 'accountant1@school.com',
            'role': CustomUser.Role.ACCOUNTANT,
            'is_active': True
        }
    )

    if created:
        accountant.set_password('password123')
        accountant.save()
        print(f"  Created accountant user: accountant1 / password123")
    else:
        print(f"  Accountant user already exists")

    return accountant


def create_fee_structures(classes):
    """Create FeeStructure records for all classes and terms"""
    print("Creating fee structures...")
    academic_year = "2024-2025"
    structure_count = 0

    # Base tuition fees per class (increases with grade)
    base_tuition = {
        1: 5000, 2: 5500, 3: 6000, 4: 6500, 5: 7000,
        6: 7500, 7: 8000, 8: 8500, 9: 9000, 10: 9500,
    }

    for class_obj in classes:
        grade = class_obj.grade_number
        tuition = base_tuition.get(grade, 5000)

        # Create tuition fee for 4 terms
        for term in ['TERM_1', 'TERM_2', 'TERM_3', 'TERM_4']:
            term_num = int(term[-1])
            due_month = {1: 4, 2: 7, 3: 10, 4: 1}[term_num]  # Apr, Jul, Oct, Jan
            due_year = 2025 if due_month >= 4 else 2026

            structure, created = FeeStructure.objects.get_or_create(
                class_obj=class_obj,
                fee_type='TUITION',
                term=term,
                academic_year=academic_year,
                defaults={
                    'amount': Decimal(str(tuition)),
                    'due_date': date(due_year, due_month, 15),
                    'is_active': True,
                }
            )
            if created:
                structure_count += 1

        # Create annual exam fee
        exam_fee = 1500 if grade <= 5 else 2000
        structure, created = FeeStructure.objects.get_or_create(
            class_obj=class_obj,
            fee_type='EXAM',
            term='ANNUAL',
            academic_year=academic_year,
            defaults={
                'amount': Decimal(str(exam_fee)),
                'due_date': date(2025, 4, 30),
                'is_active': True,
            }
        )
        if created:
            structure_count += 1

    print(f"  Created {structure_count} fee structures")


def create_sample_payments(classes, accountant_user):
    """Create sample fee payments (~70% payment rate)"""
    print("Creating sample fee payments...")
    academic_year = "2024-2025"
    payment_count = 0
    payment_methods = ['CASH', 'UPI', 'CARD', 'CHEQUE', 'ONLINE']
    method_weights = [40, 30, 15, 10, 5]  # Cash and UPI most common

    for class_obj in classes:
        structures = FeeStructure.objects.filter(
            class_obj=class_obj,
            is_active=True,
            academic_year=academic_year,
        )

        students = Student.objects.filter(
            class_section__class_obj=class_obj,
            class_section__academic_year=academic_year,
            is_active=True,
        )

        for student in students:
            for structure in structures:
                # ~70% chance of payment
                if random.random() > 0.70:
                    continue

                # Payment date within last 90 days
                days_ago = random.randint(0, 90)
                payment_date = date.today() - timedelta(days=days_ago)

                method = random.choices(payment_methods, weights=method_weights, k=1)[0]

                # Some payments are partial (10% chance)
                if random.random() < 0.10:
                    amount = structure.amount * Decimal(str(random.uniform(0.3, 0.8)))
                    amount = amount.quantize(Decimal('1'))
                    pay_status = 'PARTIAL'
                else:
                    amount = structure.amount
                    pay_status = 'PAID'

                # Check if payment already exists
                exists = FeePayment.objects.filter(
                    student=student,
                    fee_structure=structure,
                ).exists()

                if not exists:
                    FeePayment.objects.create(
                        student=student,
                        fee_structure=structure,
                        amount_paid=amount,
                        payment_method=method,
                        payment_status=pay_status,
                        payment_date=payment_date,
                        collected_by=accountant_user,
                    )
                    payment_count += 1

    print(f"  Created {payment_count} sample fee payments")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("Starting database seeding...")
    print("=" * 60)

    # Create all data
    classes = create_classes()
    sections = create_sections()
    class_sections = create_class_sections(classes, sections)
    subjects = create_subjects()
    exam_types = create_exam_types()
    create_students(class_sections)
    create_teachers(subjects, class_sections)
    create_admin()
    accountant = create_accountant()
    create_fee_structures(classes)
    create_sample_payments(classes, accountant)

    print("=" * 60)
    print("Database seeding completed successfully!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  Classes: {Class.objects.count()}")
    print(f"  Sections: {Section.objects.count()}")
    print(f"  Class Sections: {ClassSection.objects.count()}")
    print(f"  Students: {Student.objects.count()}")
    print(f"  Subjects: {Subject.objects.count()}")
    print(f"  Exam Types: {ExamType.objects.count()}")
    print(f"  Teachers: {Teacher.objects.count()}")
    print(f"  Fee Structures: {FeeStructure.objects.count()}")
    print(f"  Fee Payments: {FeePayment.objects.count()}")
    print(f"  Total Users: {CustomUser.objects.count()}")
    print("\nLogin Credentials:")
    print("  Admin: admin / admin123")
    print("  Teachers: teacher1 to teacher5 / password123")
    print("  Accountant: accountant1 / password123")
    print("=" * 60)


if __name__ == '__main__':
    main()
