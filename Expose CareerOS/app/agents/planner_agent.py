from app.agents.observer_agent import ObservationSnapshot

class WeeklyPlan:
    def __init__(self, topics: list, expected_salary_gain: float, expected_readiness_gain: float):
        self.topics = topics
        self.expected_salary_gain = expected_salary_gain
        self.expected_readiness_gain = expected_readiness_gain

    def to_dict(self) -> dict:
        return {
            "topics": self.topics,
            "expected_salary_gain": self.expected_salary_gain,
            "expected_readiness_gain": self.expected_readiness_gain
        }

class DailyPlan:
    def __init__(self, tasks: list, expected_readiness_gain: float):
        self.tasks = tasks
        self.expected_readiness_gain = expected_readiness_gain

    def to_dict(self) -> dict:
        return {
            "tasks": self.tasks,
            "expected_readiness_gain": self.expected_readiness_gain
        }

def plan_career_actions(snapshot: ObservationSnapshot) -> tuple[WeeklyPlan, DailyPlan]:
    """
    Formulates a weekly learning plan and daily tasks based on the current
    missing skills and high-demand markets detected in the snapshot.
    """
    # 1. Weekly Plan Topics selection
    weekly_topics = list(snapshot.missing_skills[:3])
    if not weekly_topics:
        weekly_topics = ["System Design", "Microservices"]
    if snapshot.new_high_demand_skill and snapshot.new_high_demand_skill not in weekly_topics:
        if len(weekly_topics) >= 3:
            weekly_topics[-1] = snapshot.new_high_demand_skill
        else:
            weekly_topics.append(snapshot.new_high_demand_skill)

    # 2. Expected weekly gains calculation
    expected_salary_gain = round(1.0 + 0.5 * len(weekly_topics), 1)
    expected_readiness_gain = round(2.5 * len(weekly_topics), 1)

    weekly_plan = WeeklyPlan(
        topics=weekly_topics,
        expected_salary_gain=expected_salary_gain,
        expected_readiness_gain=expected_readiness_gain
    )

    # 3. Daily tasks generation
    daily_tasks = []
    first_topic = weekly_topics[0] if weekly_topics else "System Design"
    daily_tasks.append(f"Complete {first_topic} Module study.")
    daily_tasks.append(f"Practice {first_topic} Interview Questions in Academy.")
    daily_tasks.append("Review 3 new job opportunities matched by system.")

    daily_plan = DailyPlan(
        tasks=daily_tasks,
        expected_readiness_gain=round(expected_readiness_gain / 5.0, 1)
    )

    return weekly_plan, daily_plan
