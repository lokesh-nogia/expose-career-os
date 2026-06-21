from sqlalchemy.orm import Session
from app.models.domain import UserProfile, QuestionBank, CompanyQuestionPattern

def seed_data(db: Session) -> None:
    """Seeds default user profile, curated question bank, and company question patterns."""
    # 1. Seed Empty User Profile for Onboarding
    if db.query(UserProfile).count() == 0:
        empty_profile = UserProfile(
            full_name="",
            current_role="",
            experience_years=0,
            current_salary=0.0,
            target_role="",
            target_salary=0.0,
            target_timeline="6 Months",
            is_onboarded=False
        )
        db.add(empty_profile)
        db.commit()
        print("Seeded: Default Empty User Profile")

    # 2. Seed Curated Question Bank
    if db.query(QuestionBank).count() == 0:
        curated_questions = [
            # Java Core
            {"question": "Explain the difference between JDK, JRE, and JVM.", "category": "Java Core", "difficulty": "Beginner", "tags": "jvm,architecture"},
            {"question": "How does Garbage Collection work in Java? Describe GC generations.", "category": "Java Core", "difficulty": "Advanced", "tags": "gc,memory"},
            {"question": "What is ClassLoader in Java? Describe the delegation model.", "category": "Java Core", "difficulty": "Senior", "tags": "classloader,security"},
            # Collections
            {"question": "Explain the difference between ArrayList and LinkedList.", "category": "Collections", "difficulty": "Beginner", "tags": "list,datastructure"},
            {"question": "How does HashMap work internally in Java 8+? What is treeification?", "category": "Collections", "difficulty": "Advanced", "tags": "hashmap,hashing"},
            {"question": "Compare Fail-Fast and Fail-Safe Iterators with examples.", "category": "Collections", "difficulty": "Senior", "tags": "iterator,concurrency"},
            # Concurrency
            {"question": "What is the difference between starting a thread with run() and start()?", "category": "Concurrency", "difficulty": "Beginner", "tags": "thread,basics"},
            {"question": "Explain volatile keyword, Java Memory Model (JMM), and instruction reordering.", "category": "Concurrency", "difficulty": "Advanced", "tags": "volatile,jmm"},
            {"question": "How do ReentrantLock, Semaphore, and CountDownLatch differ?", "category": "Concurrency", "difficulty": "Senior", "tags": "locks,synchronization"},
            {"question": "Explain ThreadLocal memory leaks and how to prevent them.", "category": "Concurrency", "difficulty": "Staff", "tags": "threadlocal,memory"},
            # Spring Boot
            {"question": "What is Dependency Injection in Spring?", "category": "Spring Boot", "difficulty": "Beginner", "tags": "di,ioc"},
            {"question": "Explain Spring Bean Scopes and bean lifecycle callbacks.", "category": "Spring Boot", "difficulty": "Intermediate", "tags": "beans,lifecycle"},
            {"question": "How does @Transactional propagation work? Explain REQUIRED vs REQUIRES_NEW.", "category": "Spring Boot", "difficulty": "Advanced", "tags": "transactions,aop"},
            {"question": "How does Spring Boot Auto-Configuration work under the hood?", "category": "Spring Boot", "difficulty": "Senior", "tags": "autoconfig,annotations"},
            # Microservices
            {"question": "What is a Microservice Architecture?", "category": "Microservices", "difficulty": "Beginner", "tags": "basics,patterns"},
            {"question": "Explain the API Gateway pattern and its benefits.", "category": "Microservices", "difficulty": "Intermediate", "tags": "gateway,routing"},
            {"question": "How do you implement the Saga Pattern for distributed transactions?", "category": "Microservices", "difficulty": "Senior", "tags": "saga,transactions"},
            {"question": "Describe Circuit Breaker pattern with Resilience4j states.", "category": "Microservices", "difficulty": "Senior", "tags": "resilience,circuitbreaker"},
            # Kafka
            {"question": "What is a Kafka topic and how are partitions distributed?", "category": "Kafka", "difficulty": "Intermediate", "tags": "topic,partition"},
            {"question": "Explain Kafka Consumer Groups, partition rebalancing, and offset committing.", "category": "Kafka", "difficulty": "Advanced", "tags": "consumer,rebalance"},
            {"question": "How do you achieve exactly-once processing semantics in Kafka?", "category": "Kafka", "difficulty": "Staff", "tags": "exactlyonce,semantics"},
            # Docker
            {"question": "What is a Docker container vs virtual machine?", "category": "Docker", "difficulty": "Beginner", "tags": "containers,virtualization"},
            {"question": "Explain Docker multi-stage builds and why they are useful.", "category": "Docker", "difficulty": "Intermediate", "tags": "builds,optimization"},
            {"question": "How do you secure containerized applications and reduce image size?", "category": "Docker", "difficulty": "Advanced", "tags": "security,bestpractices"},
            # AWS
            {"question": "What is AWS EC2 vs S3?", "category": "AWS", "difficulty": "Beginner", "tags": "ec2,s3,compute"},
            {"question": "Explain IAM roles, security groups, and VPC subnet routing.", "category": "AWS", "difficulty": "Intermediate", "tags": "iam,vpc,networking"},
            {"question": "Design a highly available multi-region serverless API on AWS.", "category": "AWS", "difficulty": "Senior", "tags": "serverless,architecture"},
            # System Design
            {"question": "Design a URL Shortener like Bitly.", "category": "System Design", "difficulty": "Intermediate", "tags": "urlshortener,basics"},
            {"question": "Design a rate limiter for APIs (Token Bucket vs Leaky Bucket).", "category": "System Design", "difficulty": "Advanced", "tags": "ratelimiter,api"},
            {"question": "Design a distributed caching system (LRU, write-back vs write-through).", "category": "System Design", "difficulty": "Senior", "tags": "caching,distributed"},
            {"question": "Design a notification system at the scale of WhatsApp.", "category": "System Design", "difficulty": "Staff", "tags": "notifications,scale"},
            # Behavioral
            {"question": "Tell me about a time you had a technical disagreement with a teammate.", "category": "Behavioral", "difficulty": "Intermediate", "tags": "star,conflict"},
            {"question": "Describe a complex bug you solved and what you learned.", "category": "Behavioral", "difficulty": "Senior", "tags": "debugging,problem"},
            {"question": "How do you manage technical debt in a fast-paced delivery setup?", "category": "Behavioral", "difficulty": "Staff", "tags": "techdebt,management"}
        ]
        for q in curated_questions:
            db.add(QuestionBank(**q))
        db.commit()
        print(f"Seeded: {len(curated_questions)} Curated QuestionBank items")

    # 3. Seed Company Question Patterns
    if db.query(CompanyQuestionPattern).count() == 0:
        patterns = [
            {"company": "Amazon", "category": "Concurrency", "frequency": 12, "difficulty": "Advanced"},
            {"company": "Amazon", "category": "System Design", "frequency": 18, "difficulty": "Senior"},
            {"company": "Google", "category": "System Design", "frequency": 22, "difficulty": "Senior"},
            {"company": "Google", "category": "Concurrency", "frequency": 8, "difficulty": "Advanced"},
            {"company": "Stripe", "category": "Spring Boot", "frequency": 6, "difficulty": "Intermediate"},
            {"company": "Stripe", "category": "System Design", "frequency": 15, "difficulty": "Senior"},
            {"company": "Atlassian", "category": "Java Core", "frequency": 10, "difficulty": "Intermediate"},
            {"company": "Uber", "category": "System Design", "frequency": 14, "difficulty": "Senior"},
            {"company": "Microsoft", "category": "Docker", "frequency": 7, "difficulty": "Intermediate"}
        ]
        for p in patterns:
            db.add(CompanyQuestionPattern(**p))
        db.commit()
        print("Seeded: Company Question Patterns")

