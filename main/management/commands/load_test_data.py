import random

from django.core.management.base import BaseCommand

from main.models import Memory


class Command(BaseCommand):
    help = "Load test data for Memory model to test filtering functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of test memories to create (default: 50)",
        )

    def handle(self, *args, **options):
        count = options["count"]

        # Clear existing memories
        Memory.objects.all().delete()
        self.stdout.write(self.style.WARNING("Cleared existing memories"))

        # Sample data for diverse testing
        countries = [
            "US",
            "GB",
            "CA",
            "AU",
            "DE",
            "FR",
            "ES",
            "IT",
            "JP",
            "BR",
            "IN",
            "ZA",
        ]
        ages = list(range(1, 19))
        genders = ["BOY", "GIRL", "OTHER", "PREFER_NOT_TO_SAY"]
        heritages = [
            "White/Caucasian",
            "Black/African American",
            "Hispanic/Latino",
            "Asian",
            "Native American",
            "Pacific Islander",
            "Mixed Race",
            "Middle Eastern",
            "South Asian",
            "East Asian",
            "European",
        ]
        school_grades = [
            "Kindergarten",
            "1st Grade",
            "2nd Grade",
            "3rd Grade",
            "4th Grade",
            "5th Grade",
            "6th Grade",
            "7th Grade",
            "8th Grade",
            "9th Grade",
            "10th Grade",
            "11th Grade",
            "12th Grade",
            "Freshman",
            "Sophomore",
            "Junior",
            "Senior",
            "Year 1",
            "Year 2",
            "Year 3",
            "Year 4",
            "Year 5",
            "Year 6",
            "Year 7",
            "Year 8",
            "Year 9",
            "Year 10",
            "Year 11",
            "Year 12",
        ]
        school_fundings = [
            "GOVERNMENT_STATE",
            "FAMILY",
            "SCHOLARSHIP_DONATIONS",
            "OTHER",
        ]
        custom_school_fundings = [
            "Mixed Funding",
            "Church Funding",
            "Community Funded",
        ]
        locations = [
            "London",
            "Manchester",
            "New York City",
            "Los Angeles",
            "Chicago",
            "Toronto",
            "Vancouver",
            "Sydney",
            "Melbourne",
            "Berlin",
            "Paris",
            "Tokyo",
            "Mumbai",
            "São Paulo",
        ]
        educational_philosophies = [
            "MONTESSORI",
            "WALDORF",
            "REGGIO_EMILIA",
            "PROGRESSIVE",
            "INTERNATIONAL_BACCALAUREATE",
            "FOREST_SCHOOL",
            "HOMESCHOOLING",
            "DOES_NOT_APPLY",
        ]
        religious_traditions = [
            "QUAKER",
            "CATHOLIC",
            "PROTESTANT_CHRISTIAN",
            "JEWISH",
            "MUSLIM",
            "HINDU",
            "BUDDHIST",
            "GREEK_ORTHODOX",
            "DOES_NOT_APPLY",
        ]

        # Memory themes for variety
        themes_list = [
            "Bullying",
            "Friendship",
            "Teachers",
            "Sports",
            "Academic Pressure",
            "Social Anxiety",
            "Cafeteria Food",
            "School Dances",
            "Exams",
            "Graduation",
            "First Day",
            "Homework",
            "Recess",
            "Art Class",
            "Music Class",
            "PE Class",
            "Science Experiments",
            "Field Trips",
            "School Bus",
            "Uniforms",
            "Crushes",
            "Drama Club",
            "Student Council",
            "Detention",
            "School Spirit",
            "Peer Pressure",
            "Class Projects",
            "School Lunch",
            "Library",
            "Playground",
            "Study Groups",
            "School Rules",
            "Principal",
            "School Assemblies",
            "Yearbook",
            "Prom",
            "Homecoming",
            "School Newspaper",
            "Band",
            "Choir",
            "Debate Team",
            "Science Fair",
            "Awards Ceremony",
        ]

        sample_memories = [
            {
                "title": "The Day I Made My Best Friend",
                "body": "I remember walking into the cafeteria on my first day at a new school, feeling completely lost and alone. Everyone seemed to already have their groups, and I was standing there with my lunch tray, looking for somewhere to sit. Then this girl with curly hair and a bright smile waved me over to her table. She introduced herself and her friends, and just like that, I had found my people. That simple act of kindness changed everything for me, and we stayed best friends throughout high school.",
            },
            {
                "title": "Science Fair Victory",
                "body": "I spent weeks working on my volcano project for the science fair. I was so nervous about presenting it because I had always been shy in front of crowds. But when the judges came to my station, something clicked. I explained how the chemical reaction worked with such enthusiasm that I forgot to be nervous. When they announced I had won first place, I could barely believe it. That moment taught me that passion can overcome fear.",
            },
            {
                "title": "The Cafeteria Food Incident",
                "body": 'Our school cafeteria was notorious for its questionable food choices, but nothing prepared us for the day they served what they called "mystery meat." It was supposed to be some kind of casserole, but it looked like nothing any of us had ever seen before. My friend dared me to try it, and against my better judgment, I took a bite. The taste was indescribable - not necessarily bad, but definitely not identifiable. We all started laughing so hard that the lunch lady came over to see what was wrong.',
            },
            {
                "title": "Standing Up to the Bully",
                "body": "There was this kid in my grade who thought he owned the playground. He would push smaller kids around and take their lunch money. I watched it happen for weeks, feeling too scared to do anything about it. But one day, I saw him pick on my younger brother, and something inside me snapped. I marched right up to him and told him to stop. My voice was shaking, but I stood my ground. He looked surprised that someone had finally stood up to him, and from that day on, he left my brother alone.",
            },
            {
                "title": "The Great Exam Mix-Up",
                "body": "I had studied for weeks for my final history exam. I knew every date, every battle, every important figure from the Civil War unit we had covered. When I sat down and opened the test booklet, my heart sank. It was the geography exam. Somehow, the teachers had mixed up the test papers. I looked around and saw other students with the same confused expression. We all raised our hands at the same time, and the teacher realized the mistake. We got to retake the exam the next day, but those few minutes of panic are burned into my memory forever.",
            },
            {
                "title": "Drama Club Dreams",
                "body": "I had always wanted to be in the school play, but I was too nervous to audition. My drama teacher, Mrs. Johnson, encouraged me to try out for the spring production of Romeo and Juliet. I practiced my monologue for hours in front of my bedroom mirror. When audition day came, my hands were shaking as I walked onto the stage. But as soon as I started speaking, all my nerves disappeared. I felt like I was transported to another world. I got a small part in the ensemble, but it felt like I had won an Oscar.",
            },
            {
                "title": "The Substitute Teacher Day",
                "body": "Our regular math teacher was out sick, and we had this young substitute who looked barely older than us seniors. Some of my classmates thought it would be funny to test her limits and see what they could get away with. But instead of getting flustered, she handled everything with such grace and humor that by the end of class, we were all actually engaged in learning algebra. She taught us that respect has nothing to do with age and everything to do with how you carry yourself.",
            },
            {
                "title": "Graduation Day Reflections",
                "body": "As I sat in that hot gymnasium, wearing my cap and gown, waiting for my name to be called, I couldn't help but think about all the memories I had made in these halls. The friends I had gained and lost, the teachers who had believed in me, the moments of triumph and failure that had shaped who I was becoming. When I walked across that stage and received my diploma, I felt like I was closing one chapter of my life and opening another. It was terrifying and exciting at the same time.",
            },
        ]

        memories_created = 0

        for i in range(count):
            # Pick random sample memory or create variations
            base_memory = random.choice(sample_memories)

            # Create variations of the title and add some randomness
            title_variations = [
                base_memory["title"],
                f"My {base_memory['title'].lower()}",
                f"Remembering {base_memory['title'].lower()}",
                f"The story of {base_memory['title'].lower()}",
                f"When {base_memory['title'].lower()} happened",
            ]

            # Select school funding and handle custom types
            school_funding = random.choice(school_fundings)
            school_funding_other = None
            if school_funding == "OTHER":
                school_funding_other = random.choice(custom_school_fundings)

            # Select educational philosophy (0-3 philosophies)
            educational_philosophy_count = random.randint(0, 3)
            if educational_philosophy_count > 0:
                selected_philosophies = random.sample(educational_philosophies, educational_philosophy_count)
                educational_philosophy = ",".join(selected_philosophies)
            else:
                educational_philosophy = None

            # Select religious tradition (optional)
            religious_tradition = random.choice(religious_traditions) if random.random() < 0.5 else None

            # Create main themes (1-3 themes)
            main_themes_count = random.randint(1, 3)
            main_themes = random.sample(themes_list, main_themes_count)
            memory_themes = ", ".join(main_themes)

            # Sometimes add additional themes
            memory_themes_additional = None
            if random.random() < 0.3:  # 30% chance of additional themes
                additional_count = random.randint(1, 2)
                # Make sure we don't repeat themes
                available_additional = [t for t in themes_list if t not in main_themes]
                if available_additional:
                    additional_themes = random.sample(
                        available_additional,
                        min(additional_count, len(available_additional)),
                    )
                    memory_themes_additional = ", ".join(additional_themes)

            memory = Memory.objects.create(
                age=random.choice(ages),
                location=random.choice(locations),
                country=random.choice(countries),
                gender=random.choice(genders),
                heritage=random.choice(heritages),
                school_grade=random.choice(school_grades),
                school_funding=school_funding,
                school_funding_other=school_funding_other,
                educational_philosophy=educational_philosophy,
                religious_tradition=religious_tradition,
                memory_themes=memory_themes,
                memory_themes_additional=memory_themes_additional,
                title=random.choice(title_variations),
                body=base_memory["body"] + f" [Memory #{i + 1}]",
            )
            memories_created += 1

            if memories_created % 10 == 0:
                self.stdout.write(f"Created {memories_created} memories...")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {memories_created} test memories!"
            )
        )

        # Print summary statistics
        self.stdout.write("\n--- Filter Test Coverage ---")
        self.stdout.write(
            f"Ages: {Memory.objects.values_list('age', flat=True).distinct().count()}"
        )
        self.stdout.write(
            f"Locations: {Memory.objects.values_list('location', flat=True).distinct().count()}"
        )
        self.stdout.write(
            f"Countries: {Memory.objects.values_list('country', flat=True).distinct().count()}"
        )
        self.stdout.write(
            f"Genders: {Memory.objects.values_list('gender', flat=True).distinct().count()}"
        )
        self.stdout.write(
            f"Heritages: {Memory.objects.values_list('heritage', flat=True).distinct().count()}"
        )
        self.stdout.write(
            f"School Grades: {Memory.objects.values_list('school_grade', flat=True).distinct().count()}"
        )
        self.stdout.write(
            f"School Fundings: {Memory.objects.values_list('school_funding', flat=True).distinct().count()}"
        )

        # Count unique themes across both fields
        all_themes = set()
        for memory in Memory.objects.all():
            if memory.memory_themes:
                themes = [t.strip() for t in memory.memory_themes.split(",")]
                all_themes.update(themes)
            if memory.memory_themes_additional:
                themes = [t.strip() for t in memory.memory_themes_additional.split(",")]
                all_themes.update(themes)

        self.stdout.write(f"Memory Themes: {len(all_themes)}")
        self.stdout.write("\nAll filters should now have options to test with!")
