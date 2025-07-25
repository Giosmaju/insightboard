from . import db
from app import bcrypt
from sqlalchemy import CheckConstraint
import datetime
from datetime import date, timedelta
from flask import abort
from sqlalchemy import func

class User(db.Model):
    __tablename__ = 'user'
    entries = db.relationship('Entry', back_populates = 'user')
    analytics = db.relationship('Analytics', back_populates = 'user')

    def set_password(self, password):
        self.hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.hashed_password, password)

    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    hashed_password = db.Column(db.String(1000), nullable=False)

class Entry(db.Model):
    __tablename__ = 'entries'
    user = db.relationship('User', back_populates = 'entries')
    
    @classmethod
    def entry_filtering(cls, user_id, **kwargs):
        start_date = kwargs.get('start_date', None)
        end_date = kwargs.get('end_date', None)

        category = kwargs.get('category', None)

        min_rating = kwargs.get('min_rating', None)
        max_rating = kwargs.get('max_rating', None)

        min_duration = kwargs.get('min_duration', None)
        max_duration = kwargs.get('max_duration', None)

        status = kwargs.get('status', None)

        if (start_date == None and end_date == None):
            start_time = datetime.time(00, 00)
            end_time = datetime.time(23, 59)

            start_date = datetime.datetime.combine(date.today(), start_time)

            target_weekday = 7 # For Sunday

            # Get today's date
            today = date.today()

            if (today.isoweekday() == 7):
                days_to_add = 7
            else:
                # Calculate the difference in days to reach the target weekday
                days_to_add = (target_weekday - today.isoweekday() + 7) % 7

            # Get the date of the next occurrence of the target weekday
            target_day = today + timedelta(days=days_to_add)

            end_date = datetime.datetime.combine(target_day, end_time)
        
        entries = Entry.query.filter(cls.user_id == user_id, cls.start_time.between(start_date, end_date)).order_by(cls.start_time)

        if (category):
            entries = entries.filter(cls.category == category)

        if (min_rating and max_rating):
            entries = entries.filter(cls.rating.between(min_rating, max_rating))
        
        if (min_duration and max_duration):
            entries = entries.filter(cls.duration.between(min_duration, max_duration))

        if (status):
            entries = entries.filter(cls.status == status)

        final_entries = entries.all()
        
        return final_entries
    
    @staticmethod
    def to_dict(entry_list):
        result = []
        for entry in entry_list:
            temp = dict([("task_name", entry.task_name), ("category", entry.category), ("start_time", entry.start_time.isoformat()), 
                         ("end_time", entry.end_time.isoformat()), ("rating", entry.rating), ("status", entry.status)])
                          
            result.append(temp)
        
        return result
    
    @staticmethod
    def status_verification(status):
        valid_status = ["scheduled", "completed", "in progress"]
        if (status.strip().lower() in valid_status):
            return True
        else:
            return False
    
    @staticmethod
    def rating_verification(rating):
        valid_ratings = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        if (rating in valid_ratings):
            return True
        else:
            return False
        
    @classmethod
    def status_change(cls, user_id, task_id, up_status):
        entry = Entry.query.filter(cls.user_id == user_id, cls.id == task_id).first()

        if (entry == None):
            abort(404, description="Entry does not exist")

        verify = Entry.status_verification(up_status)

        if(verify):
            entry.status = up_status
            db.session.commit()
            return True
        else:
            return False

    
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_name = db.Column(db.String(40), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer)
    status = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Integer)
    notes = db.Column(db.String(100))

    __table_args__ = (CheckConstraint('rating BETWEEN 1 AND 10', name='rating_constraint'),)

class Analytics(db.Model):
    __tablename__ = 'analytics'
    user = db.relationship('User', back_populates = 'analytics')

    @classmethod
    def week_summary(cls, user_id):
        start_time = datetime.time(0, 0)
        end_time = datetime.time(23, 59)

        target_weekday_start = 1  # Monday
        target_weekday_end = 7    # Sunday

        today = datetime.date.today()
        days_to_sub_start = (target_weekday_start - today.isoweekday() - 7)
        days_to_sub_end = (target_weekday_end - today.isoweekday() - 7)

        weekday_start = today + timedelta(days=days_to_sub_start)
        weekday_end = today + timedelta(days=days_to_sub_end)

        start_date = datetime.datetime.combine(weekday_start, start_time)
        end_date = datetime.datetime.combine(weekday_end, end_time)

        data = Entry.query.filter(
            Entry.user_id == user_id,
            Entry.start_time.between(start_date, end_date)
        )

        tasks_total = data.count()
        if tasks_total == 0:
            return {
                "scheduled": 0,
                "completed": 0,
                "in_progress": 0,
                "note": "No tasks were logged this past week"
            }

        tasks_scheduled = (data.filter(Entry.status == 'scheduled').count() / tasks_total) * 100
        tasks_completed = (data.filter(Entry.status == 'completed').count() / tasks_total) * 100
        tasks_in_progress = (data.filter(Entry.status == 'in progress').count() / tasks_total) * 100

        average_rating = db.session.query(func.avg(Entry.rating)).filter(
            Entry.user_id == user_id,
            Entry.start_time.between(start_date, end_date)
        ).scalar()

        average_task_duration = db.session.query(func.avg(Entry.duration)).filter(
            Entry.user_id == user_id,
            Entry.start_time.between(start_date, end_date)
        ).scalar()


        top_category = db.session.query(
            Entry.category,
            func.count(Entry.id)
        ).filter(
            Entry.user_id == user_id,
            Entry.start_time.between(start_date, end_date)
        ).group_by(Entry.category).order_by(func.count(Entry.id).desc()).first()


        top_completed_day = db.session.query(
            func.date(Entry.start_time),
            func.count(Entry.status)
        ).filter(
            Entry.user_id == user_id,
            Entry.start_time.between(start_date, end_date),
            Entry.status == "completed"
        ).group_by(
            func.date(Entry.start_time)
        ).order_by(func.count(Entry.id).desc()).all()


        top_rating_day = db.session.query(
            func.date(Entry.start_time),
            func.avg(Entry.rating)
        ).filter(
            Entry.user_id == user_id,
            Entry.start_time.between(start_date, end_date)
        ).group_by(
            func.date(Entry.start_time)
        ).order_by(func.avg(Entry.rating).desc()).all()

        completed_dict = {date: count for date, count in top_completed_day}
        rating_dict = {date: avg_rating for date, avg_rating in top_rating_day}

        best_day = None
        weighted_score = 0
        for date in completed_dict:
            if date in rating_dict:
                score = completed_dict[date] * float(rating_dict[date])
                if score > weighted_score:
                    weighted_score = score
                    best_day = date

        return {
            "scheduled": tasks_scheduled,
            "completed": tasks_completed,
            "in_progress": tasks_in_progress,
            "average_rating": average_rating,
            "average_task_duration": average_task_duration,
            "most_active_day": best_day,
            "top_category": top_category[0] if top_category else None,
        }

    @staticmethod
    def weekly_summary(user_id):
        print("Running weekly summary task...")
        summary = Analytics.week_summary(user_id)

        analytic_entry = Analytics(
            user_id=user_id,
            week_start=date.today() - timedelta(days=date.today().weekday() + 7),  # previous Monday
            week_end=date.today() - timedelta(days=date.today().weekday() + 1),    # previous Sunday
            tasks_scheduled=summary["scheduled"],
            tasks_completed=summary["completed"],
            tasks_in_progress=summary["in_progress"],
            average_rating=float(summary["average_rating"]),
            average_task_duration=float(summary["average_task_duration"]),
            most_active_day = summary["most_active_day"],
            top_category=summary["top_category"]
        )

        db.session.add(analytic_entry)
        print(f"User ID {user_id} summary saved.")

        db.session.commit()

    @classmethod
    def get_first(cls, user_id):
        analytic_entries = Analytics.query.filter(cls.user_id == user_id).order_by(cls.week_start.desc()).first()

        if (analytic_entries == None):
            abort(404, description="No tasks logged last week")

        dict_analytics = dict([("week_start", analytic_entries.week_start.isoformat()), ("week_end", analytic_entries.week_end.isoformat()), 
                               ("tasks_scheduled", analytic_entries.tasks_scheduled), ("tasks_completed", analytic_entries.tasks_completed), 
                               ("tasks_in_progress", analytic_entries.tasks_in_progress), ("average_rating", analytic_entries.average_rating), 
                               ("average_task_duration", analytic_entries.average_task_duration), ("most_active_day", analytic_entries.most_active_day), 
                               ("top_category", analytic_entries.top_category)])

        return dict_analytics

    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    week_start = db.Column(db.DateTime, nullable = False)
    week_end = db.Column(db.DateTime, nullable = False)
    tasks_scheduled = db.Column(db.Float)
    tasks_completed = db.Column(db.Float)
    tasks_in_progress = db.Column(db.Float)
    average_rating = db.Column(db.Integer)
    average_task_duration = db.Column(db.Integer)
    most_active_day = db.Column(db.String(10))
    top_category = db.Column(db.String(40))