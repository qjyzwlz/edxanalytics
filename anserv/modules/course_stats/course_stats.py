import logging
log = logging.getLogger(__name__)
log.error("BLAH")
from modules.decorators import view, query, event_handler, memoize_query
#from an_evt.models import StudentBookAccesses
from django.contrib.auth.models import User

import json
from django.conf import settings
import logging
from django.utils import timezone
import datetime
from modules import common, tasks
import sys
from django.contrib.auth.models import User
import csv
from pymongo import MongoClient
connection = MongoClient()

log=logging.getLogger(__name__)
import re
import os
from django.http import HttpResponse

import courseware

from courseware.models import StudentModule

from mitxmako.shortcuts import render_to_response, render_to_string

@query('course', 'total_user_count')
def users_in_course_count_query(fs, db, course,params):
    return users_in_course_query(fs,db,course,params).count()

@query('course', 'all_users')
def users_in_course_query(fs, db, course,params):
    return StudentModule.objects.filter(course_id=course).values('student').distinct()

@query('course', 'modules_accessed_count')
def modules_accessed_in_course_count_query(fs, db, course, params):
    return StudentModule.objects.filter(course_id=course).count()

@query('course', 'problems_tried_count')
def problems_tried_in_course_count_query(fs, db, course, params):
    return StudentModule.objects.filter(course_id=course,module_type="problem").count()

@query('course', 'video_watch_count')
def videos_watched_in_course_count_query(fs, db, course, params):
    return StudentModule.objects.filter(course_id=course,module_type="video").count()

@view('course', 'total_user_count')
def users_in_course_count_view(fs, db, course, params):
    return "The system has "+str(users_in_course_count_query(fs,db,course,params)) + " users total"

@view('course', 'modules_accessed_count')
def modules_accessed_in_course_count_view(fs, db, course, params):
    return str(modules_accessed_in_course_count_query(fs,db,course,params)) + " modules accessed in the course."

@view('course', 'problems_tried_count')
def problems_tried_in_course_count_view(fs, db, course, params):
    return str(problems_tried_in_course_count_query(fs,db,course,params)) + " problems tried in the course."

@view('course', 'video_watch_count')
def videos_watched_in_course_count_view(fs, db, course, params):
    return str(videos_watched_in_course_count_query(fs,db,course,params)) + "videos watched in the course."

@query('global', 'users_per_course_count')
def users_per_course_count_query():
    query_string = "SELECT course_id, COUNT(DISTINCT user_id) AS count FROM student_courseenrollment GROUP BY course_id"
    return common.query_results(query_string)

@view('global', 'users_per_course')
def users_per_course_count_view():
    query_data = users_per_course_count_query()
    return common.render_query_as_table(query_data)

@query('global', 'new_students')
@memoize_query(cache_time=15*60)
def new_course_enrollment_query(fs, db, params):
    r = common.query_results("SELECT course_id,COUNT(DISTINCT student_id) FROM `courseware_studentmodule` WHERE DATE(created) >= DATE(DATE_ADD(NOW(), INTERVAL -7 DAY)) GROUP BY course_id;")
    return r

@view('global', 'new_students')
def new_course_enrollment_view(fs, db, params):
    r = new_course_enrollment_query(fs,db,params)
    return common.render_query_as_table(r)

@query('global', 'available_courses')
def courses_available_query(fs, db, params):
    r = [c['course_id'] for c in StudentModule.objects.all().values('course_id').distinct()]
    return r

@query('course', 'student_grades')
def course_grades_query(fs,db,course, params):
    collection = connection['modules_tasks']['student_problem_stats']
    course_name = re.sub("[/:]","_",course)
    json_data = list(collection.find({'course' : course}))

    if len(json_data)<1:
        return {'success' : False, 'message' : "Cannot find the course in the list or data not available.", 'courses' : courses_available_query(fs,db,params)}
    json_data = json_data[0]

    json_data = {k:json_data[k] for k in json_data if k in ["course", "updated", "results"]}
    csv_file = "{0}/{1}_{2}.csv".format(settings.PROTECTED_DATA_URL,"student_grades",course_name)
    return {'csv' : csv_file, 'json' : json_data, 'success' : True}

@query('course', 'student_problem_grades')
def problem_grades_query(fs,db,course, params):
    collection = connection['modules_tasks']['student_course_stats']
    course_name = re.sub("[/:]","_",course)
    json_data = list(collection.find({'course' : course}))

    if len(json_data)<1:
        return {'success' : False, 'message' : "Cannot find the course in the list or data not available." , 'courses' : courses_available_query(fs,db,params)}
    json_data = json_data[0]

    json_data = {k:json_data[k] for k in json_data if k in ["course", "updated", "results"]}
    csv_file = "{0}/{1}_{2}.csv".format(settings.PROTECTED_DATA_URL,"student_problem_grades",course_name)
    return {'csv' : csv_file, 'json' : json_data}
