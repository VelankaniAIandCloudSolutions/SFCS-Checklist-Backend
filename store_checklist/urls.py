from django.urls import path
from store_checklist import views

urlpatterns = [


    path('upload-bom/', views.upload_bom_task),
    path('scan-code/', views.scan_code),
    path('assign_defect_type/', views.assign_defect_type),
    path('get-boms/', views.get_boms),
    path('get-checklist-report/', views.get_checklist_report),
    path('get-boms/<int:bom_id>/', views.get_bom_by_id),
    path('generate-new-checklist/<int:order_id>/', views.generate_new_checklist),
    path('get-active-checklist/<int:bom_id>/', views.get_active_checklist),
    path('check-existing-checklist/<int:bom_id>/',
         views.check_existing_checklist),

    path('get-passed-checklists/', views.get_passed_checklists),
    path('end-checklist/<int:checklist_id>/', views.end_checklist),
    path('get-checklist-details/<int:checklist_id>/',
         views.get_checklist_details),
    path('get-iqc-data/<int:checklist_id>/', views.get_iqc_data),
    path('save-qr-code/<int:checklist_id>/', views.save_qr_code),
    path('generated-checklists/<int:bom_id>/', views.get_checklists_for_bom),
    path('get-checklist-count/', views.get_checklist_count),
    path('check-task-status/<str:task_id>/', views.check_task_status),

    path('edit-bom-line-item/<int:bom_line_item_id>/', views.edit_bom_line_item),
    path('delete-bom-line-item/<int:bom_line_item_id>/',
         views.delete_bom_line_item),
    path('update-checklist-item/<int:checklist_item_id>/',
         views.update_checklist_item),



    path('get-orders/', views.get_orders),

    path('create-order/', views.create_order),
    path('create-order/<int:project_id>/', views.create_order),
    path('create-order-task/', views.create_order_task),
    path('delete-order/<int:order_id>/', views.delete_order),


    path('create-project/', views.create_project),
    path('edit-project/', views.edit_project),
    path('edit-project/<int:project_id>/', views.edit_project),
    path('delete-project/<int:project_id>/', views.delete_project),




    path('create-product/', views.create_product),
    path('create-product/<int:project_id>/', views.create_product),
    path('edit-product/<int:product_id>/', views.edit_product),
    path('delete-product/<int:product_id>/', views.delete_product),

    path('upload-iqc-file/', views.upload_iqc_file),
    path('handle-bom-cases/', views.handle_bom_cases),
    path('pause-checklist/<int:checklist_id>/', views.pause_checklist),
    path('resume-checklist/<int:checklist_id>/', views.resume_checklist),
    path('get-inspection-board-data/',
         views.get_inspection_board_data),
    path('create-defect-type/', views.create_defect_type),
    path('get-inspection-boards/', views.get_inspection_boards)






    #     path('toggle-checklist-settings/<int:checklist_id>/',views.toggle_checklist_settings)

    #     path('upload-new-bom/', views.upload_new_bom)

    #     path('get-products/<int:project_id>/', views.get_products_by_project),
    #     path('get-projects/', views.get_projects),
    #     path('get-orders/', views.get_orders),
    #     path('get-boms-without-line-items/', views.get_boms_without_line_items)




]
