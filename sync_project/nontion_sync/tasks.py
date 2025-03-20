import logging
from sync_project.celery import app
from celery import chain
from .models import NotionDbConfig
from .notion_connector import (
    NotionConnector, NotionServiceReportConnector,
    NotionResponsibleReportConnector, NotionBuReportConnector, 
    WorkloadCalculator, NotionWorkloadSync, NotionWorkloadtempSync, WorkloadTempCalculator, NotionProjects, NotionTasks
)
logger = logging.getLogger(__name__)

@app.task
def sync_notion_tasks(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True,database_id="1313a17e5d7f81be9daec933d18a74ed")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing tasks data from database: {config.database_id}")

        try:
            connector = NotionTasks(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            result = connector.sync_tasks()
            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")

@app.task
def sync_notion_projects(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True,database_id="1313a17e5d7f816a8ffae10bfb920f43")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing orders data from database: {config.database_id}")

        try:
            connector = NotionProjects(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            result = connector.sync_projects()
            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")
@app.task
def sync_notion_orders(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True,database_id="13e3a17e5d7f80da9a55e1a01feda7b3")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing orders data from database: {config.database_id}")

        try:
            connector = NotionConnector(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            result = connector.sync_orders()
            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")

@app.task
def sync_notion_service_report(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True, database_id="1733a17e5d7f8009bbf6d7c68b1cacf1")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing services data to database: {config.database_id}")

        try:
            connector = NotionServiceReportConnector(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            result = connector.sync_service_report()
            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")

@app.task
def sync_notion_responsible_report(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True, database_id="1743a17e5d7f80daa1e2c6c5c7cc979c")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing responsible data to database: {config.database_id}")

        try:
            connector = NotionResponsibleReportConnector(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            result = connector.sync_service_report()
            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")

@app.task
def sync_notion_bunit_report(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True, database_id="1743a17e5d7f801b8009d5b5788e8c00")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing bunit data to database: {config.database_id}")

        try:
            connector = NotionBuReportConnector(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            result = connector.sync_service_report()
            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")

@app.task
def sync_notion_workload(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True, database_id="1763a17e5d7f80f9acf9c9618f521957")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing workload data to database: {config.database_id}")

        try:
            calculator = WorkloadCalculator(
                notion_token=config.notion_token,
                project_tasks_database_id="1313a17e5d7f81be9daec933d18a74ed",
                closing_tasks_database_id="13e3a17e5d7f804b893df6008ef0f629",
                orders_database_id="13e3a17e5d7f80da9a55e1a01feda7b3"
            )
            workload_data, workload_hours_data = calculator.calculate_workload()

            syncer = NotionWorkloadSync(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            # Оновлена логіка для синхронізації нових полів
            result = syncer.sync_workload(workload_data, workload_hours_data)

            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")


@app.task
def sync_notion_workloadtemporary(*args, **kwargs):
    configs = NotionDbConfig.objects.filter(is_active=True, database_id="17a3a17e5d7f80369544c30b2953d9ba")
    if not configs.exists():
        logger.error("No active NotionDbConfig records found.")
        print("❌ No active configurations.")
        return

    for config in configs:
        logger.info(f"Processing NotionDbConfig: {config.name}")
        print(f"🔄 Syncing workload data to database: {config.database_id}")

        try:
            calculator = WorkloadTempCalculator(
                notion_token=config.notion_token,
                project_tasks_database_id="1313a17e5d7f81be9daec933d18a74ed",
                closing_tasks_database_id="13e3a17e5d7f804b893df6008ef0f629",
                orders_database_id="13e3a17e5d7f80da9a55e1a01feda7b3"
            )
            workload_data = calculator.calculate_workload()

            syncer = NotionWorkloadtempSync(
                notion_token=config.notion_token,
                database_id=config.database_id
            )
            result = syncer.sync_workload(workload_data)

            logger.info(f"✅ Sync result for {config.database_id}: {result}")
            print(f"✅ {result}")
        except Exception as e:
            logger.error(f"Error syncing database {config.database_id}: {str(e)}")
            print(f"❌ Error: {str(e)}")


@app.task
def execute_tasks():
    # Виконання задач по черзі
    chain(
        sync_notion_orders.s(),
        sync_notion_service_report.s(),
        sync_notion_responsible_report.s(),
        sync_notion_bunit_report.s(),
        
    )()