from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
from .tasks import execute_tasks, sync_notion_workloadtemporary,sync_notion_orders, sync_notion_service_report, sync_notion_responsible_report, sync_notion_bunit_report, sync_notion_workload

logger = logging.getLogger(__name__)
API_KEY = "notionpinok123pinok"
@csrf_exempt
def run_task(request):
    
    api_key = request.GET.get("api_key")
    if api_key != API_KEY:
        return JsonResponse({"status": "error", "message": "Unauthorized request."})
    
    if request.method in ["POST", "GET"]:
        try:
            sync_notion_orders()
            # sync_notion_workloadtemporary()
            sync_notion_service_report()
            sync_notion_responsible_report()
            sync_notion_bunit_report()
            sync_notion_workload()

            logger.info("Task triggered from Notion button!")
            return JsonResponse({"status": "success", "message": "Task has been started and updatet data!"})
        
        except Exception as e:
            logger.error(f"Error while starting task: {e}")
            return JsonResponse({"status": "error", "message": str(e)})
    
    return JsonResponse({"status": "error", "message": "Invalid request method."})
