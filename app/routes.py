from flask import Flask,Blueprint, jsonify, request
from app import db
from app.models import User, Entry, Analytics
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager
from datetime import datetime, time, date, timedelta
from flask import abort
from app.auth_utils import admin_required

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    return jsonify({"message": "Backend is working!"})

@bp.route("/login", methods = ['POST'])
def login():
    if (request.method == 'POST'):
        payload = request.json

        username = payload['username']
        password = payload['password']

        user_check = User.query.filter_by(username = username).first()

        if(user_check == None):
            raise KeyError from None
        
        pw_check = user_check.check_password(password)

        if(pw_check):

            if(user_check.admin):
                additional_claims = {'priv': 'admin'}
                access_token = create_access_token(identity = str(user_check.id), additional_claims = additional_claims)
                refresh_token = create_refresh_token(identity = str(user_check.id), additional_claims = additional_claims)
            else:
                access_token = create_access_token(identity = str(user_check.id))
                refresh_token = create_refresh_token(identity = str(user_check.id))

            return jsonify(access_token = access_token, refresh_token = refresh_token)
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

@bp.route("/refresh", methods = ['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token = access_token)

@bp.route("/protected", methods = ['GET'])
@jwt_required(refresh = False)
def protected():
    return jsonify({"message": "Access granted", "user_id": get_jwt_identity()})

@bp.route("/signup", methods = ["POST"])
def signup():
    payload = request.json

    username = payload['username']
    email = payload['email']
    password = payload['password']

    new_user = User(username = username, email = email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True, "message": "Correctly registered user"}), 200

@bp.route("/entries", methods = ['POST'])
@jwt_required()
def fill_entry():
    current_user_id = get_jwt_identity()

    payload = request.json

    task_name = payload['task_name']
    category = payload['category']
    str_start_time = payload['start_time']
    str_end_time = payload['end_time']
    rating = payload['rating']
    status = payload['status']
    notes = payload['notes']

    format_str = "%Y-%m-%d %H:%M"
    start_time = datetime.strptime(str_start_time, format_str)
    end_time = datetime.strptime(str_end_time, format_str)

    delta_duration = end_time - start_time
    duration = int((end_time - start_time).total_seconds() / 60)

    status_verification = Entry.status_verification(status)
    if (status_verification == False):
        abort(400, description="Invalid status. Must be 'scheduled', 'completed', or 'in progress'.")

    rating_verification = Entry.rating_verification(rating)
    if (rating_verification == False):
        abort(400, description="Invalid rating. Must be a number between 1 and 10, inclusive")

    new_entry = Entry(user_id = int(current_user_id), task_name = task_name, category = category, start_time = start_time, 
                      end_time = end_time, duration = duration, status= status, rating = rating, notes = notes)

    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'success': True, 'message': "Entry has been successfully made"}), 200

@bp.route("/entries", methods = ['GET'])
@jwt_required()
def filtering():
    current_user_id = get_jwt_identity()

    str_start = request.args.get('start_time', None)
    str_end = request.args.get('end_time', None)
    category = request.args.get('category', None)
    str_min_rating = request.args.get('min_rating', None)
    str_max_rating = request.args.get('max_rating', None)
    str_min_duration = request.args.get('min_duration', None)
    str_max_duration = request.args.get('max_duration', None)
    status = request.args.get('status', None)

    if (str_start and str_end):
        format_str = "%Y-%m-%d %H:%M"
        start_time = datetime.strptime(str_start, format_str)
        end_time = datetime.strptime(str_end, format_str)
    else:
        start_time = None
        end_time = None

    if (str_min_rating and str_max_rating):
        min_rating = int(str_min_rating)
        max_rating = int(str_max_rating)
    else:
        min_rating = None
        max_rating = None
    
    if (str_min_duration and str_max_duration):
        min_duration = int(str_min_duration)
        max_duration = int(str_max_duration)
    else:
        min_duration = None
        max_duration = None
    
    filter_params = {
    'start_date': start_time,
    'end_date': end_time,
    'category': category,
    'min_rating': min_rating,
    'max_rating': max_rating,
    'min_duration': min_duration,
    'max_duration': max_duration,
    'status': status
    }

    entries = Entry.entry_filtering(current_user_id, **filter_params)
    entries_dict = Entry.to_dict(entries)

    return jsonify(entries_dict)

@bp.route("/entry_status_update", methods = ['POST'])
@jwt_required()
def status_update():
    current_user_id = get_jwt_identity()
    payload = request.json

    task_id = payload['task_id']
    new_status = payload['new_status']

    strp_status = new_status.strip().lower()

    stat_up = Entry.status_change(current_user_id, task_id, strp_status)

    if (stat_up):
        return jsonify({'success': True, 'message': "Entry status successfully updated"}), 200
    else:
        abort(400, description="Invalid status. Must be 'scheduled', 'completed', or 'in progress'.")

@bp.route("/admin/analytics", methods=["GET"])
@jwt_required()
@admin_required
def all_summaries():
    week_start=date.today() - timedelta(days=date.today().weekday() + 7)  # previous Monday
    week_end=date.today() - timedelta(days=date.today().weekday() + 1)    # previous Sunday

    summaries = Analytics.query.filter(
        Analytics.week_start >= week_start,
        Analytics.week_end <= week_end
    ).all()

    dict_analytics_list = []
    for row in summaries:
        dict_analytics = {
            "week_start": row.week_start.isoformat(),
            "week_end": row.week_end.isoformat(),
            "tasks_scheduled": row.tasks_scheduled,
            "tasks_completed": row.tasks_completed,
            "tasks_in_progress": row.tasks_in_progress,
            "average_rating": row.average_rating,
            "average_task_duration": row.average_task_duration,
            "most_active_day": row.most_active_day,
            "top_category": row.top_category
        }
        dict_analytics_list.append(dict_analytics)

    return jsonify(dict_analytics_list), 200

@bp.route("/analytics", methods = ['GET'])
@jwt_required()
def weekly_summary():
    current_user_id = get_jwt_identity()

    analytics_summary = Analytics.get_first(current_user_id)
    
    return jsonify(analytics_summary), 200


