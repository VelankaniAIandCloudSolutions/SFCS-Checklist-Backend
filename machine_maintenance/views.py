
# from rest_framework.response import JsonResponse
from .serializers import MaintenanceActivitySerializer
from .models import MaintenanceActivity
import json
from .models import MaintenancePlan, MaintenanceActivity
from django.http import JsonResponse
from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import calendar


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

#             # Get the selected machine object

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

#                                 # num_days_in_month = calendar.monthrange(
#                                 #     selected_year, list(calendar.month_abbr).index(matched_month))[1]

#                                 selected_year = int(selected_year)

#                                 num_days_in_month = calendar.monthrange(
#                                     selected_year, month_index)[1]

#                                 print('num_days_in_month', num_days_in_month)

#                                 # Get the starting day of the first week of the month
#                                 first_day_of_month = datetime.strptime(
#                                     f'{selected_year}-{month}-01', '%Y-%B-%d').date()

#                                 print('first_day_of_month', first_day_of_month)
#                                 starting_weekday = first_day_of_month.weekday()
#                                 # Adjust starting week if the first day of the month is not Monday
#                                 print('starting_weekday', starting_weekday)

#                                 # if starting week is 0 that menas monday we set starting_weekday to monday otherwise 1
#                                 starting_week = 0 if starting_weekday == 0 else 1

#                                 selected_day_indices = [
#                                     list(calendar.day_name).index(day) for day in selected_days]

#                                 print('selected_day_indices',
#                                       selected_day_indices)

#                                 # Loop through the weeks of the month
#                                 for week_num in selected_weeks:
#                                     print('selected_weeks', selected_weeks)

#                                     # Calculate the week number
#                                     week_number = int(week_num.split()[1])
#                                     # week_start = (
#                                     #     int(week_num.split()[1]) - starting_week) * 7 + 1
#                                     print('week number', week_number)

#                                     week_start = ((week_number - 1) * 7) - \
#                                         starting_weekday + 1

#                                     week_start = max(1, week_start)

#                                     print('week_start', week_start)

#                                     week_end = min(
#                                         week_start + 6, num_days_in_month)

#                                     # Calculate the start date of the week
#                                     # week_start = (week_num.split()[1] - 1) * 7 + 1
#                                     # print('week_start', week_start)
#                                     # week_end = min(week_num.split()[
#                                     #                1] * 7, num_days_in_month)
#                                     print('week_end', week_end)

#                                     print('selected_days', selected_days)

#                                     for day_int in range(week_start, week_end + 1):
#                                         # Get the day of the week index (0 for Monday, 1 for Tuesday, ..., 6 for Sunday)
#                                         day_of_week_index = (
#                                             day_int - 1 + starting_weekday) % 7

#                                         # Check if the day of the week index is among the selected day indices
#                                         if day_of_week_index in selected_day_indices:
#                                             print('Month title case:',
#                                                   month_title_case.capitalize())
#                                             print('Month abbreviations:',
#                                                   list(calendar.month_abbr))

#                                             # Create the maintenance date using selected_year, month_index, and the current day integer
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

#                         return JsonResponse({'message': 'Maintenance activities created successfully'}, status=201)

#                 except Machine.DoesNotExist:
#                     return JsonResponse({'error': 'Machine not found'}, status=404)
#     except MaintenanceActivityType.DoesNotExist:
#         return JsonResponse({'error': 'Maintenance activity type not found'}, status=404)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


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

                                    week_start = (
                                        (week_number - 1) * 7) - starting_weekday + 1
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
