"""
Seed real KAAF University programmes from the official website.
Usage: python manage.py seed_kaaf_programmes
"""
from django.core.management.base import BaseCommand


KAAF_DATA = [
    {
        'faculty': 'Faculty of Health and Allied Sciences',
        'code': 'FHAS',
        'programmes': [
            ('BSC-GN',   'BSc General Nursing',              4),
            ('BSC-MID',  'BSc Midwifery',                    4),
            ('BSC-PHN',  'BSc Public Health Nursing',        4),
            ('DMLS',     'Doctor of Medical Laboratory Science', 6),
            ('PHARMD',   'Doctor of Pharmacy (PharmD)',      6),
        ]
    },
    {
        'faculty': 'Faculty of Business Administration',
        'code': 'FBA',
        'programmes': [
            ('BSC-ACC',  'BSc Accounting',                   4),
            ('BSC-MKT',  'BSc Marketing',                    4),
        ]
    },
    {
        'faculty': 'Faculty of Engineering',
        'code': 'FENG',
        'programmes': [
            ('BSC-CS',   'BSc Computer Science',             4),
            ('BSC-IT',   'BSc Information Technology',       4),
            ('BSC-CT',   'BSc Construction Technology',      4),
        ]
    },
    {
        'faculty': 'Faculty of Law and Political Science',
        'code': 'FLPS',
        'programmes': [
            ('LLB',      'LLB Law',                          4),
        ]
    },
]


class Command(BaseCommand):
    help = 'Seed real KAAF University programmes and departments'

    def handle(self, *args, **options):
        from apps.students.models import Department, Programme

        created_depts = 0
        created_progs = 0

        for faculty_data in KAAF_DATA:
            dept, created = Department.objects.get_or_create(
                code=faculty_data['code'],
                defaults={
                    'name': faculty_data['faculty'].replace('Faculty of ', ''),
                    'faculty': faculty_data['faculty'],
                }
            )
            if created:
                created_depts += 1

            for code, name, duration in faculty_data['programmes']:
                _, created = Programme.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'department': dept,
                        'duration_years': duration,
                    }
                )
                if created:
                    created_progs += 1

        self.stdout.write(self.style.SUCCESS(
            f'✅ Done — {created_depts} departments, {created_progs} programmes created.'
        ))
        self.stdout.write('Programmes now available on the signup page.')
