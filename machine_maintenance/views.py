
# from rest_framework.response import JsonResponse
from datetime import datetime
from .serializers import MaintenanceActivitySerializer
from .models import MaintenanceActivity
import json
from .models import MaintenancePlan, MaintenanceActivity
from django.http import JsonResponse
from django.shortcuts import render
from .models import *
from .serializers import *
from datetime import datetime, timedelta
import calendar
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from .tasks import *
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def get_machine_data(request):
    try:
        lines = Line.objects.all()
        machines = Machine.objects.all()
        models = Model.objects.all()
        maintenance_activity_type = MaintenanceActivityType.objects.all()

        line_serializer = LineSerializer(lines, many=True)
        model_serializer = ModelSerializer(models, many=True)
        machine_serializer = MachineSerializerNew(machines, many=True)
        maintenance_activity_type_serializer = MaintenanceActivityTypeSerializer(
            maintenance_activity_type, many=True)

        return Response({
            'machines': machine_serializer.data,
            'lines': line_serializer.data,
            'models': model_serializer.data,
            'maintenance_activity_types': maintenance_activity_type_serializer.data,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_maintenance_plan(request):
    try:
        if request.method == 'POST':
            # Extract form data from the request
            data = request.data
            current_user = request.user

            # Get selected machine ID from the form data
            selected_machine_ids = data.get('selectedMachines', [])
            print('selected_machine_ids', selected_machine_ids)

            selected_type_id = data.get('selectedType')
            print('selected_type_id', selected_type_id)

            selected_type = MaintenanceActivityType.objects.get(
                pk=selected_type_id)
            print('selected_type', selected_type)

            # Loop through each selected machine
            for machine_id in selected_machine_ids:
                try:
                    selected_machine = Machine.objects.get(pk=machine_id)
                    print('selected_machine', selected_machine)

                    # Loop through each year in the data
                    years_from_frontend = data.get('selectedYears', [])
                    print('year from front-end', years_from_frontend)

                    for selected_year in data.get('selectedYears', []):
                        # Loop through each choice in the year
                        print('selected_year inside first loop', selected_year)

                        for choice in data.get('dateChoices', {}).get('choices', []):
                            # Extract selected months and weeks from the choice
                            selected_months = choice.get('selectedMonths', [])
                            selected_weeks = choice.get('selectedWeeks', [])
                            selected_days = choice.get('selectedDays', [])

                            # Loop through the selected months
                            for month in selected_months:
                                print("Selected month:", month)
                                print('calendar.moth_abbr',
                                      list(calendar.month_abbr))

                                # Convert month to title case for better matching
                                month_title_case = month.title()
                                print('month_title_case', month_title_case)

                                # Partial matching logic
                                matched_month = None
                                for abbr in calendar.month_abbr:
                                    if abbr and abbr.lower() in month_title_case.lower():  # Partial match
                                        print('match found')
                                        matched_month = abbr
                                        print('matched_month', matched_month)
                                        break

                                if not matched_month:
                                    print(
                                        f"Error: '{month}' does not match any valid month abbreviation")
                                    # Handle the error accordingly
                                    continue

                                month_abbr_list = list(calendar.month_abbr)
                                print('month_abbr_list', month_abbr_list)

                                month_index = month_abbr_list.index(
                                    matched_month)
                                print('month_index', month_index)

                                selected_year = int(selected_year)

                                num_days_in_month = calendar.monthrange(
                                    selected_year, month_index)[1]
                                print('num_days_in_month', num_days_in_month)

                                first_day_of_month = datetime.strptime(
                                    f'{selected_year}-{month}-01', '%Y-%B-%d').date()
                                print('first_day_of_month', first_day_of_month)
                                starting_weekday = first_day_of_month.weekday()
                                print('starting_weekday', starting_weekday)

                                starting_week = 0 if starting_weekday == 0 else 1

                                selected_day_indices = [
                                    list(calendar.day_name).index(day) for day in selected_days]
                                print('selected_day_indices',
                                      selected_day_indices)

                                for week_num in selected_weeks:
                                    print('selected_weeks', selected_weeks)

                                    week_number = int(week_num.split()[1])
                                    print('week number', week_number)

                                    week_start = (week_number - 1) * 7 + 1
                                    week_start = max(1, week_start)
                                    print('week_start', week_start)

                                    week_end = min(
                                        week_start + 6, num_days_in_month)
                                    print('week_end', week_end)

                                    print('selected_days', selected_days)

                                    for day_int in range(week_start, week_end + 1):
                                        day_of_week_index = (
                                            day_int - 1 + starting_weekday) % 7

                                        if day_of_week_index in selected_day_indices:
                                            print('Month title case:',
                                                  month_title_case.capitalize())
                                            print('Month abbreviations:',
                                                  list(calendar.month_abbr))

                                            maintenance_date = datetime(
                                                selected_year, month_index, day_int)

                                            print('Maintenance date:',
                                                  maintenance_date)

                                            # Create MaintenanceActivity object
                                            maintenance_plan = MaintenancePlan.objects.create(
                                                maintenance_date=maintenance_date,
                                                machine=selected_machine,
                                                maintenance_activity_type=selected_type,
                                                description=None,
                                                created_by=current_user,
                                                updated_by=current_user
                                            )

                                            maintenance_plan.save()
                                            print(
                                                'Maintenance activity created successfully')

                except Machine.DoesNotExist:
                    return JsonResponse({'error': 'Machine not found'}, status=404)

            return JsonResponse({'message': 'Maintenance activities created successfully'}, status=201)

    except MaintenanceActivityType.DoesNotExist:
        return JsonResponse({'error': 'Maintenance activity type not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# @api_view(['POST'])
# def create_maintenance_plan(request):
#     try:
#         if request.method == 'POST':
#             # Extract form data from the request
#             data = request.data
#             current_user = request.user

#             # Get selected machine ID from the form data
#             selected_machine_ids = data.get('selectedMachines', [])
#             print('selected_machine_ids', selected_machine_ids)

#             selected_type_id = data.get('selectedType')
#             print('selected_type_id', selected_type_id)

#             selected_type = MaintenanceActivityType.objects.get(
#                 pk=selected_type_id)
#             print('selected_type', selected_type)

#             # Loop through each selected machine
#             for machine_id in selected_machine_ids:
#                 try:
#                     selected_machine = Machine.objects.get(pk=machine_id)
#                     print('selected_machine', selected_machine)

#                     # Loop through each year in the data
#                     years_from_frontend = data.get('selectedYears', [])
#                     print('year from front-end', years_from_frontend)

#                     for selected_year in data.get('selectedYears', []):
#                         # Loop through each choice in the year
#                         print('selected_year inside first loop', selected_year)

#                         for choice in data.get('dateChoices', {}).get('choices', []):
#                             # Extract selected months and weeks from the choice
#                             selected_months = choice.get('selectedMonths', [])
#                             selected_weeks = choice.get('selectedWeeks', [])
#                             selected_days = choice.get('selectedDays', [])

#                             # Loop through the selected months
#                             for month in selected_months:
#                                 print("Selected month:", month)
#                                 print('calendar.moth_abbr',
#                                       list(calendar.month_abbr))

#                                 # Convert month to title case for better matching
#                                 month_title_case = month.title()
#                                 print('month_title_case', month_title_case)

#                                 # Partial matching logic
#                                 matched_month = None
#                                 for abbr in calendar.month_abbr:
#                                     if abbr and abbr.lower() in month_title_case.lower():  # Partial match
#                                         print('match found')
#                                         matched_month = abbr
#                                         print('matched_month', matched_month)
#                                         break

#                                 if not matched_month:
#                                     print(
#                                         f"Error: '{month}' does not match any valid month abbreviation")
#                                     # Handle the error accordingly
#                                     continue

#                                 month_abbr_list = list(calendar.month_abbr)
#                                 print('month_abbr_list', month_abbr_list)

#                                 month_index = month_abbr_list.index(
#                                     matched_month)
#                                 print('month_index', month_index)

#                                 selected_year = int(selected_year)

#                                 num_days_in_month = calendar.monthrange(
#                                     selected_year, month_index)[1]
#                                 print('num_days_in_month', num_days_in_month)

#                                 first_day_of_month = datetime.strptime(
#                                     f'{selected_year}-{month}-01', '%Y-%B-%d').date()
#                                 print('first_day_of_month', first_day_of_month)
#                                 starting_weekday = first_day_of_month.weekday()
#                                 print('starting_weekday', starting_weekday)

#                                 starting_week = 0 if starting_weekday == 0 else 1

#                                 selected_day_indices = [
#                                     list(calendar.day_name).index(day) for day in selected_days]
#                                 print('selected_day_indices',
#                                       selected_day_indices)

#                                 for week_num in selected_weeks:
#                                     print('selected_weeks', selected_weeks)

#                                     week_number = int(week_num.split()[1])
#                                     print('week number', week_number)

#                                     week_start = (week_number - 1) * 7 + 1
#                                     week_start = max(1, week_start)
#                                     print('week_start', week_start)

#                                     week_end = min(
#                                         week_start + 6, num_days_in_month)
#                                     print('week_end', week_end)

#                                     print('selected_days', selected_days)

#                                     for day_int in range(week_start, week_end + 1):
#                                         day_of_week_index = (
#                                             day_int - 1 + starting_weekday) % 7

#                                         if day_of_week_index in selected_day_indices:
#                                             print('Month title case:',
#                                                   month_title_case.capitalize())
#                                             print('Month abbreviations:',
#                                                   list(calendar.month_abbr))

#                                             maintenance_date = datetime(
#                                                 selected_year, month_index, day_int)

#                                             print('Maintenance date:',
#                                                   maintenance_date)

#                                             # Create MaintenanceActivity object
#                                             maintenance_plan = MaintenancePlan.objects.create(
#                                                 maintenance_date=maintenance_date,
#                                                 machine=selected_machine,
#                                                 maintenance_activity_type=selected_type,
#                                                 description=None,
#                                                 created_by=current_user,
#                                                 updated_by=current_user
#                                             )

#                                             maintenance_plan.save()
#                                             print(
#                                                 'Maintenance activity created successfully')

#                 except Machine.DoesNotExist:
#                     return JsonResponse({'error': 'Machine not found'}, status=404)

#             return JsonResponse({'message': 'Maintenance activities created successfully'}, status=201)

#     except MaintenanceActivityType.DoesNotExist:
#         return JsonResponse({'error': 'Maintenance activity type not found'}, status=404)

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def create_maintenance_plan_for_all_machines_of_a_line(request):
    try:
        if request.method == 'POST':
            # Extract data from the request
            data = request.data
            current_user = request.user

            # Extract parameters from the request data
            selected_year = data.get('selectedYear')
            selected_month = data.get('selectedMonth')
            selected_line_id = data.get('selectedLine')
            selected_type_id = data.get('selectedType')
            selected_custom_filter = data.get('selectedCustomFilter')

            # Validate inputs if needed
            if not all([selected_year, selected_month, selected_line_id, selected_type_id, selected_custom_filter]):
                return JsonResponse({'error': 'Missing required parameters'}, status=400)

            # Retrieve line and activity type objects
            selected_line = Line.objects.get(pk=selected_line_id)
            selected_type = MaintenanceActivityType.objects.get(
                pk=selected_type_id)

            # Convert month name to its abbreviation
            def get_month_abbr(month_name):
                month_abbr = calendar.month_abbr[1:]
                month_names = calendar.month_name[1:]
                month_dict = dict(zip(month_names, month_abbr))
                return month_dict.get(month_name)

            selected_month_abbr = get_month_abbr(selected_month)
            if selected_month_abbr is None:
                return JsonResponse({'error': 'Invalid month name'}, status=400)

            # Get all machines belonging to the selected line
            selected_machines = Machine.objects.filter(line=selected_line)

            # Determine the number of days in the selected month
            num_days_in_month = calendar.monthrange(int(selected_year), list(
                calendar.month_abbr).index(selected_month_abbr))[1]

            if selected_custom_filter == 'wholeMonth':
                # Loop through each machine
                for machine in selected_machines:
                    # Loop through each day in the month
                    for day_int in range(1, num_days_in_month + 1):
                        maintenance_date = datetime(int(selected_year), list(
                            calendar.month_abbr).index(selected_month_abbr), day_int)

                        # Create MaintenanceActivity object
                        maintenance_plan = MaintenancePlan.objects.create(
                            maintenance_date=maintenance_date,
                            machine=machine,
                            maintenance_activity_type=selected_type,
                            description=None,
                            created_by=current_user,
                            updated_by=current_user
                        )

                        maintenance_plan.save()
            else:
                # Handle other custom filter options here
                pass

            return JsonResponse({'message': 'Maintenance activities created successfully'}, status=201)

    except Line.DoesNotExist:
        return JsonResponse({'error': 'Line not found'}, status=404)

    except MaintenanceActivityType.DoesNotExist:
        return JsonResponse({'error': 'Maintenance activity type not found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def get_maintenance_plan(request):
    if request.method == 'POST':
        # Step 1: Extract machine ID from the request
        machine_id = request.data.get('machine_id')
        print(machine_id)
        # Step 2: Retrieve maintenance plans filtered by machine ID and sorted by maintenance date
        maintenance_plans = MaintenancePlan.objects.filter(
            machine_id=machine_id).order_by('maintenance_date')
        # Step 3: Serialize the maintenance plans
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        # Step 4: Return serialized maintenance plans in the response
        return Response({"maintenance_plans": serializer.data})


@api_view(['POST'])
def get_maintenance_plan_new_line_wise(request):
    if request.method == 'POST':
        # Step 1: Extract line ID from the request
        line_id = request.data.get('line_id')

        # Step 2: Retrieve the first machine associated with the line
        try:
            machine = Machine.objects.filter(line=line_id).first()
        except Machine.DoesNotExist:
            return Response({"error": "No machine found for the given line ID"}, status=status.HTTP_404_NOT_FOUND)

        # Step 3: Retrieve maintenance plans filtered by machine ID and sorted by maintenance date
        maintenance_plans = MaintenancePlan.objects.filter(
            machine=machine)

        # Step 4: Serialize the maintenance plans
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        # Step 4: Return serialized maintenance plans in the response
        return Response({"maintenance_plans": serializer.data})


@api_view(['DELETE'])
def delete_maintenance_plan(request, maintenance_plan_id):
    if request.method == 'DELETE':

        print('this is the maintenance plan id coming form url', maintenance_plan_id)

        try:
            maintenance_plan = MaintenancePlan.objects.get(
                id=maintenance_plan_id)
        except MaintenancePlan.DoesNotExist:
            return Response({'error': 'Maintenance Plan not found'}, status=404)

        maintenance_plan.delete()

        remaining_maintenance_plans = MaintenancePlan.objects.all()
        serializer = MaintenancePlanSerializer(
            remaining_maintenance_plans, many=True)

        return Response({'message': 'Maintenance plan deleted successfully', 'maintenance_plans': serializer.data}, status=200)


@api_view(['POST'])
def create_maintenance_activity(request):
    if request.method == 'POST':
        maintenance_plan_id = request.data.get('id')
        note = request.data.get('note', '')
        created_by = request.user  # Assuming you have authentication set up
        updated_by = request.user

        try:
            maintenance_plan = MaintenancePlan.objects.get(
                id=maintenance_plan_id)
            maintenance_activity, created = MaintenanceActivity.objects.get_or_create(
                maintenance_plan=maintenance_plan,
                defaults={'note': note, 'created_by': created_by,
                          'updated_by': updated_by}
            )
            if not created:
                maintenance_activity.note = note
                maintenance_activity.updated_by = updated_by
                maintenance_activity.save()
        except MaintenancePlan.DoesNotExist:
            return JsonResponse({'error': f'Maintenance plan with id {maintenance_plan_id} does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # Serialize all maintenance plans with their related activities
        maintenance_plans = MaintenancePlan.objects.all()
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        return JsonResponse({'message': 'Maintenance activity created/updated successfully', 'maintenance_plans': serializer.data}, status=201)


@api_view(['POST'])
def create_maintenance_activity_new(request):
    if request.method == 'POST':
        maintenance_plan_id = request.data.get('id')
        line_id = request.data.get('line_id')
        machine_id = request.data.get('machine_id')
        note = request.data.get('note', '')
        is_completed = request.data.get(
            'maintenance_activity_status', False)

        print('is completed', is_completed)

        # assuming it's boolean
        created_by = request.user  # Assuming you have authentication set up
        updated_by = request.user

        try:
            maintenance_plan = MaintenancePlan.objects.get(
                id=maintenance_plan_id)
            maintenance_activity, created = MaintenanceActivity.objects.get_or_create(
                maintenance_plan=maintenance_plan,
                defaults={'note': note, 'created_by': created_by,
                          'updated_by': updated_by, 'is_completed': is_completed}
            )
            if not created:
                maintenance_activity.note = note
                maintenance_activity.updated_by = updated_by
                maintenance_activity.is_completed = is_completed
                maintenance_activity.save()

        except MaintenancePlan.DoesNotExist:
            return JsonResponse({'error': f'Maintenance plan with id {maintenance_plan_id} does not exist'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # Serialize all maintenance plans with their related activities
        maintenance_plan = MaintenancePlan.objects.get(pk=maintenance_plan_id)

        maintenance_plan_machine = maintenance_plan.machine
        maintenance_plans = MaintenancePlan.objects.filter(
            machine=maintenance_plan_machine)
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        # maintenance_plans = MaintenancePlan.objects.filter(
        #     machine_id=machine_id)
        # serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        return JsonResponse({'message': 'Maintenance activity created/updated successfully', 'maintenance_plans': serializer.data}, status=201)


@api_view(['POST'])
def create_maintenance_activity_new_for_all_machines_of_a_line(request):
    if request.method == 'POST':
        line_id = request.data.get('line_id')
        note = request.data.get('note', '')
        created_by = request.user  # Assuming you have authentication set up
        updated_by = request.user
        clicked_maintenance_date = request.data.get('clicked_maintenance_date')
        maintenance_plan_id = request.data.get('maintenance_plan_id')

        try:
            # Retrieve machines on the given line
            machines = Machine.objects.filter(line=line_id)

            # Retrieve or validate the provided maintenance plan
            try:
                maintenance_plan = MaintenancePlan.objects.get(
                    id=maintenance_plan_id)
            except MaintenancePlan.DoesNotExist:
                return JsonResponse({'error': f'Maintenance plan with id {maintenance_plan_id} does not exist'}, status=400)

            # Create maintenance activities for all machines on the line
            for machine in machines:
                # Create or get maintenance activity for the maintenance plan
                maintenance_activity, created = MaintenanceActivity.objects.get_or_create(
                    maintenance_plan=maintenance_plan,
                    defaults={'note': note, 'created_by': created_by,
                              'updated_by': updated_by}
                )
                if not created:
                    maintenance_activity.note = note
                    maintenance_activity.updated_by = updated_by
                    maintenance_activity.save()

            # Serialize maintenance plan and return
            serializer = MaintenancePlanSerializer(maintenance_plan)
            return Response({'maintenance_plan': serializer.data}, status=201)

        except Machine.DoesNotExist:
            return JsonResponse({'error': f'No machines found for the given line ID'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# @api_view(['POST'])
# def create_maintenance_activity(request):
#     if request.method == 'POST':
#         # Convert selected date from string to datetime object
#         clicked_formatted_date_str = request.data.get('clickedFormattedDate')
#         clicked_formatted_date = datetime.strptime(
#             clicked_formatted_date_str, '%Y-%m-%d').date()

#         # Other code remains the same
#         maintenance_plan_id = request.data.get('id')
#         note = request.data.get('note', '')
#         created_by = request.user  # Assuming you have authentication set up
#         updated_by = request.user
#         # Get applyToAll boolean from request
#         apply_to_all = request.data.get('applyToAll', False)

#         try:
#             if apply_to_all:  # If applyToAll is True
#                 selected_line_id = request.data.get('selectedLineID')
#                 # Get all machines belonging to the selected line
#                 machines = Machine.objects.filter(line_id=selected_line_id)
#                 for machine in machines:
#                     # Check if maintenance plan exists for the selected date
#                     maintenance_plan = MaintenancePlan.objects.filter(
#                         machine=machine, maintenance_date=clicked_formatted_date).first()
#                     if maintenance_plan:
#                         # Create or update maintenance activity for each machine
#                         maintenance_activity, created = MaintenanceActivity.objects.get_or_create(
#                             maintenance_plan=maintenance_plan,
#                             defaults={
#                                 'note': note, 'created_by': created_by, 'updated_by': updated_by}
#                         )
#                         if not created:
#                             maintenance_activity.note = note
#                             maintenance_activity.updated_by = updated_by
#                             maintenance_activity.save()
#                     else:
#                         # Handle case where maintenance plan doesn't exist for the machine
#                         pass  # You can add your custom logic here
#             else:  # If applyToAll is False
#                 # Handle single machine maintenance activity creation/update here
#                 maintenance_plan = MaintenancePlan.objects.get(
#                     id=maintenance_plan_id)
#                 maintenance_activity, created = MaintenanceActivity.objects.get_or_create(
#                     maintenance_plan=maintenance_plan,
#                     defaults={'note': note, 'created_by': created_by,
#                               'updated_by': updated_by}
#                 )
#                 if not created:
#                     maintenance_activity.note = note
#                     maintenance_activity.updated_by = updated_by
#                     maintenance_activity.save()
#         except MaintenancePlan.DoesNotExist:
#             return JsonResponse({'error': f'Maintenance plan with id {maintenance_plan_id} does not exist'}, status=400)
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#         # Serialize all maintenance plans with their related activities
#         maintenance_plans = MaintenancePlan.objects.all()
#         serializer = MaintenancePlanSerializer(maintenance_plans, many=True)
#         return JsonResponse({'message': 'Maintenance activity created/updated successfully', 'maintenance_plans': serializer.data}, status=201)


@api_view(['PUT', 'DELETE'])
def update_or_delete_maintenance_activity(request, maintenance_plan_id):
    if request.method == 'PUT':
        # Extract new note from request data
        new_note = request.data.get('note')

        # Retrieve maintenance activity object
        try:
            maintenance_activity = MaintenanceActivity.objects.get(
                maintenance_plan_id=maintenance_plan_id)
        except MaintenanceActivity.DoesNotExist:
            return Response({'error': 'Maintenance activity not found'}, status=404)

        # Update the note
        maintenance_activity.note = new_note
        maintenance_activity.save()

        # Retrieve all maintenance plans and serialize them
        maintenance_plans = MaintenancePlan.objects.all()
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        return Response({'message': 'Note updated successfully', 'maintenance_plans': serializer.data}, status=200)

    elif request.method == 'DELETE':
        # Retrieve maintenance activity object
        try:
            maintenance_activity = MaintenanceActivity.objects.get(
                maintenance_plan_id=maintenance_plan_id)
        except MaintenanceActivity.DoesNotExist:
            return Response({'error': 'Maintenance activity not found'}, status=404)

        # Delete the maintenance activity
        maintenance_activity.delete()

        # Retrieve all maintenance plans and serialize them
        maintenance_plans = MaintenancePlan.objects.all()
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        return Response({'message': 'Maintenance activity deleted successfully', 'maintenance_plans': serializer.data}, status=200)


@api_view(['PUT', 'DELETE'])
def update_or_delete_maintenance_activity_new(request, maintenance_plan_id):

    if request.method == 'PUT':
        # Extract new note and maintenance activity status from request data
        new_note = request.data.get('note')
        maintenance_activity_status = request.data.get(
            'maintenance_activity_status', False)

        # Retrieve maintenance activity object
        try:
            maintenance_activity = MaintenanceActivity.objects.get(
                maintenance_plan_id=maintenance_plan_id)
        except MaintenanceActivity.DoesNotExist:
            return Response({'error': 'Maintenance activity not found'}, status=404)

        # Update the note and maintenance activity status
        maintenance_activity.note = new_note
        maintenance_activity.is_completed = maintenance_activity_status
        maintenance_activity.save()

        maintenance_plan = MaintenancePlan.objects.get(pk=maintenance_plan_id)

        maintenance_plan_machine = maintenance_plan.machine
        maintenance_plans = MaintenancePlan.objects.filter(
            machine=maintenance_plan_machine)
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        return Response({'message': 'Note and status updated successfully', 'maintenance_plans': serializer.data}, status=200)

    elif request.method == 'DELETE':

        # Retrieve maintenance activity object
        try:
            maintenance_activity = MaintenanceActivity.objects.get(
                maintenance_plan_id=maintenance_plan_id)
        except MaintenanceActivity.DoesNotExist:
            return Response({'error': 'Maintenance activity not found'}, status=404)

        # Delete the maintenance activity
        maintenance_activity.delete()

        maintenance_plan = MaintenancePlan.objects.get(pk=maintenance_plan_id)

        maintenance_plan_machine = maintenance_plan.machine
        maintenance_plans = MaintenancePlan.objects.filter(
            machine=maintenance_plan_machine)
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        return Response({'message': 'Maintenance activity deleted successfully', 'maintenance_plans': serializer.data}, status=200)


@api_view(['POST'])
def create_maintenance_plan_by_clicking(request):
    # Extract data from request
    description = request.data.get('description')
    machine_id = request.data.get('machineId')
    selected_activity_type_id = request.data.get('selectedActivityType')
    selected_date_in_str = request.data.get('selectedDate')
    selected_date = datetime.strptime(selected_date_in_str, '%Y-%m-%d').date()
    print(selected_date)

    # Assuming you have access to the current user making the request
    current_user = request.user

    try:
        # Fetch related objects by their IDs
        machine = Machine.objects.get(id=machine_id)
        activity_type = MaintenanceActivityType.objects.get(
            id=selected_activity_type_id)

        # Create MaintenancePlan instance
        maintenance_plan = MaintenancePlan.objects.create(

            description=description,
            machine=machine,
            maintenance_activity_type=activity_type,
            maintenance_date=selected_date,
            created_by=current_user,
            updated_by=current_user
        )

        # Fetch all maintenance plans
        # all_maintenance_plans = MaintenancePlan.objects.all()

        all_maintenance_plans = MaintenancePlan.objects.filter(
            machine_id=machine_id)

        # Serialize all maintenance plans
        maintenance_plans_serializer = MaintenancePlanSerializer(
            all_maintenance_plans, many=True)
        serialized_data = maintenance_plans_serializer.data

        return Response(
            {"maintenance_plans": serialized_data},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def create_maintenance_plan_by_clicking_new_for_all_machines_of_a_line(request):
    # Extract data from request
    line_id = request.data.get('line_id')
    selected_date_in_str = request.data.get('selectedDate')
    selected_date = datetime.strptime(selected_date_in_str, '%Y-%m-%d').date()
    description = request.data.get('description', '')
    activity_type_id = request.data.get('selectedActivityType')

    # Assuming you have access to the current user making the request
    current_user = request.user

    try:
        # Fetch activity type
        activity_type = MaintenanceActivityType.objects.get(
            id=activity_type_id)

        # Fetch all machines on the given line
        machines = Machine.objects.filter(line=line_id)

        # Iterate over machines and create maintenance plans
        for machine in machines:
            # Create MaintenancePlan instance
            maintenance_plan = MaintenancePlan.objects.create(
                machine=machine,
                maintenance_date=selected_date,
                description=description,
                maintenance_activity_type=activity_type,
                created_by=current_user,
                updated_by=current_user
            )

        first_machine = machines.first()

        # Fetch all maintenance plans for the first machine
        first_machine_plans = MaintenancePlan.objects.filter(
            machine=first_machine)

        # first_machine_plan = MaintenancePlan.objects.filter(
        #     machine__line=line_id, maintenance_date=selected_date).first()

        # Serialize the first machine's maintenance plan
        serialized_first_machine_plans = MaintenancePlanSerializer(
            first_machine_plans, many=True).data

        # all_maintenance_plans = MaintenancePlan.objects.filter(
        #     machine__line=line_id, maintenance_date=selected_date)

        # Serialize all maintenance plans
        # maintenance_plans_serializer = MaintenancePlanSerializer(
        #     all_maintenance_plans, many=True)
        # serialized_data = maintenance_plans_serializer.data

        # return Response(
        #     {"maintenance_plans": serialized_first_machine_plan},
        #     status=status.HTTP_201_CREATED
        # )

        return Response(
            {"maintenance_plans": serialized_first_machine_plans},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@authentication_classes([])  # Use appropriate authentication class here
@permission_classes([])
def delete_maintenance_plan_line_wise(request):
    # Extract data from request
    line_id = request.data.get('line_id')
    selected_date_in_str = request.data.get('selectedDate')
    selected_date = datetime.strptime(selected_date_in_str, '%Y-%m-%d').date()
    activity_type_code = request.data.get('selectedActivityTypeCode')

    try:
        # Fetch the activity type based on the provided code
        activity_type = MaintenanceActivityType.objects.get(
            code=activity_type_code)

        print('acitivity type', activity_type)

        # Delete all maintenance plans for machines on the selected line, date, and activity type
        MaintenancePlan.objects.filter(machine__line=line_id, maintenance_date=selected_date,
                                       maintenance_activity_type=activity_type).delete()

        # Fetch all machines on the selected line
        machines = Machine.objects.filter(line=line_id)

        # Fetch maintenance plans for the first machine on the line
        first_machine = machines.first()
        first_machine_plans = MaintenancePlan.objects.filter(
            machine=first_machine)

        # Serialize maintenance plans for the first machine
        serialized_first_machine_plans = MaintenancePlanSerializer(
            first_machine_plans, many=True).data

        return Response(
            {"maintenance_plans": serialized_first_machine_plans},
            status=status.HTTP_200_OK
        )
    except MaintenanceActivityType.DoesNotExist:
        return Response(
            {"error": "Maintenance activity type with the specified code does not exist."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@authentication_classes([])  # Use appropriate authentication class here
@permission_classes([])
def test_maintenance_alert_email(request):
    # Get plans with no activities
    plans_with_no_activities = get_plans_with_no_activities()

    # Send maintenance activity missing email
    send_maintenance_activity_missing_mail(plans_with_no_activities)

    return Response({'message': 'Test email sent successfully'})


def get_plans_with_no_activities():
    # Define the date range for the last two days excluding today
    two_days_ago = timezone.now().date() - timezone.timedelta(days=2)
    today = timezone.now().date()

    # Filter maintenance plans scheduled in the last two days excluding today
    recent_scheduled_plans = MaintenancePlan.objects.filter(
        maintenance_date__gte=two_days_ago,
        maintenance_date__lt=today
    )

    # Initialize an array to store plans with no maintenance activities created
    plans_with_no_activities = []

    # Filter out plans without maintenance activities
    for plan in recent_scheduled_plans:
        if not plan.maintenance_activities.exists():
            plans_with_no_activities.append(plan)

    # Do something with plans_with_no_activities, like sending alerts or logging
    # For example, just printing their IDs along with maintenance dates
    for plan in plans_with_no_activities:
        print(
            f"Plan ID {plan.id} scheduled on {plan.maintenance_date} has no activities.")

    return plans_with_no_activities


def send_maintenance_activity_missing_mail(plans_with_no_activities):
    try:
        print('inside machine maintenance miss alert task')

        print(plans_with_no_activities)

        if plans_with_no_activities:  # Ensure there are plans with no activities

            # recipient_emails = [plan.created_by.email for plan in plans_with_no_activities]

            context = {
                'created_by': plans_with_no_activities[0].created_by,
                'maintenance_plans_with_no_activities': plans_with_no_activities,
                'website_link': 'https://sfcs.xtractautomation.com/machine'
                # Add other context variables as neededd
            }
            print(context)

            html_message = render_to_string(
                'maintenance_activity_missing_alert_email.html', context)
            plain_message = strip_tags(html_message)

            subject = 'Maintenance Activity Missing Alert'
            sender_email = settings.EMAIL_HOST_USER
            sender_name = 'Velankani SFCS'
            email_from = f'{sender_name} <{sender_email}>'

            # Send email
            send_mail(subject, plain_message, email_from, [
                      'katochsatvik@gmail.com'], html_message=html_message)

            print(
                f"Maintenance activity missing email sent to {plans_with_no_activities[0].created_by.email}")

    except Exception as e:
        # Handle any exceptions
        print(f"Error sending maintenance activity missing email: {e}")


@api_view(['GET'])
@authentication_classes([])  # Use appropriate authentication class here
@permission_classes([])
def get_maintenance_plans_for_report_generation(request):
    # Assuming format: "January", "February", etc.
    month = request.GET.get('month')  # Access month from request.GET
    print(month)
    # Assuming multiple machine IDs are passed as a list
    machine_ids = request.GET.getlist('machine_ids[]')
    print(machine_ids)

    month_dict = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    month_number = month_dict.get(month)
    print(month_number)

    if month_number:
        start_date = datetime(year=datetime.now().year,
                              month=month_number, day=1)
        end_date = datetime(year=datetime.now().year,
                            month=month_number % 12 + 1, day=1)
        end_date -= timedelta(days=1)

        maintenance_plans = MaintenancePlan.objects.filter(
            maintenance_date__range=[start_date, end_date],
            machine__id__in=machine_ids
        )

        # Serialize the queryset using MaintenancePlanSerializer
        serializer = MaintenancePlanSerializer(maintenance_plans, many=True)

        # Return serialized data in the response
        return JsonResponse({'maintenance_plans': serializer.data}, status=200)
    else:
        return JsonResponse({'error': 'Invalid month provided'}, status=400)
