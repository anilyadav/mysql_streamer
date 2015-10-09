# -*- coding: utf-8 -*-
import json
import sys
import time

from behave import given
from behave import then
from behave import when

sys.path.append('../../environment.py')
from environment import execute_query


DB_WAIT_TIME = 1


@given(u'a query to execute for table {table_name}')
def prepare_query_step(context, table_name):
    # context.text is the docstring follows the Given clause in feature file.
    query = context.text
    context.data['table_name'] = table_name
    context.data['query'] = query

@given(u'a expected create table statement for table {table_name}')
def set_expected_create_table_statement_step(context, table_name):
    context.data['table_name'] = table_name
    context.data['expected_create_table_statement'] = context.text
    context.data['event_type'] = 'schema_event'

@when(u'we execute the statement in {db_name} database')
def execute_statement_step(context, db_name):
    # Wait a bit time for containers to be ready
    time.sleep(DB_WAIT_TIME)
    result = execute_query(db_name, context.data['query'])

@then(u'{db_name} should have correct schema information')
def check_schema_tracker_has_correct_info(context, db_name):
    # Wait a bit time for change to happen in schema tracker db
    time.sleep(DB_WAIT_TIME)
    table_name = context.data['table_name']
    query = 'show create table {table_name}'.format(table_name=table_name)
    result = execute_query(db_name, query)
    expected = {
        'Table': table_name,
        'Create Table': context.data['expected_create_table_statement']
    }
    assert_result_correctness(result, expected)

@then(u'{db_name}.schema_event_state should have correct state information')
def check_schema_event_state_has_correct_info(context, db_name):
    # Wait a bit time for change to happen in rbr state db
    time.sleep(DB_WAIT_TIME)
    query = 'select * from schema_event_state order by time_created desc limit 1'
    result = execute_query(db_name, query)
    expected = {
        'status': 'Completed',
        'table_name': context.data['table_name'],
        'query': context.data['query'],
    }
    assert_result_correctness(result, expected)

    position = json.loads(result['position'])
    # Heartbeat serial and offset uniquely identifies a position.
    expected_position = {
        'hb_serial': context.data['heartbeat_serial'],
        'offset': context.data['offset'],
    }
    assert_result_correctness(position, expected_position)

@then(u'{db_name}.global_event_state should have correct state information')
def check_global_event_state_has_correct_info(context, db_name):
    time.sleep(DB_WAIT_TIME)
    query = 'select * from global_event_state'
    result = execute_query(db_name, query)
    expected = {
        'table_name': context.data['table_name'],
        'event_type': context.data['event_type'],
    }
    assert_result_correctness(result, expected)

def assert_result_correctness(result, expected):
    for key, value in expected.iteritems():
        assert result[key] == value
