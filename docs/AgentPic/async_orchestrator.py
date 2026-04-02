"""
AsyncAgentOrchestrator 异步任务编排图
"""
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.generic.device import Device
from diagrams.custom import Custom

graph_attr = {
    "fontsize": "45",
    "bgcolor": "white",
    "label": "AsyncAgentOrchestrator 异步任务编排",
    "fontname": "Microsoft YaHei",
}

with Diagram("异步任务编排", show=False, direction="TB", graph_attr=graph_attr):
    
    # 任务提交
    with Cluster("任务提交入口"):
        submit_task = Custom("submit_task()\n\n参数:\n- task_type: TaskType\n- user_id: str\n- input_data: Dict\n- priority: int\n\n返回：task_id", "icons/submit.png")
    
    # 任务队列管理
    with Cluster("任务队列管理"):
        tasks_dict = Storage("tasks: Dict\n所有任务记录")
        running_tasks = Storage("running_tasks: Dict\n运行中任务")
        max_concurrent = Custom("max_concurrent_tasks\n最大并发数：3", "icons/config.png")
        
        schedule_logic = Custom("调度逻辑\n\nif running < max:\n  立即执行\nelse:\n  等待调度", "icons/schedule.png")
    
    # 任务执行
    with Cluster("任务执行"):
        run_task = Custom("_run_task()\n\n1. status = RUNNING\n2. 执行对应任务\n3. 捕获异常\n4. status = COMPLETED/FAILED\n5. 记录完成时间", "icons/run.png")
        
        with Cluster("7 种任务类型处理"):
            deep_think = Custom("DEEP_THINK\n_deep_think_analysis\n\n输入:\n- message\n- conversation_history\n- user_features\n\n输出:\n- deep_analysis\n- emotional_state\n- potential_needs\n- personality_insights", "icons/think.png")
            
            feature_corr = Custom("FEATURE_CORRELATION\n_feature_correlation_analysis\n\n输入:\n- new_features\n- existing_features\n\n输出:\n- correlations\n- inferred_features", "icons/correlation.png")
            
            relationship = Custom("RELATIONSHIP_DISCOVERY\n_relationship_discovery\n\n输入:\n- message\n- conversation_history\n\n输出:\n- relationships\n- social_insights", "icons/relationship.png")
            
            memory = Custom("MEMORY_CONSOLIDATION\n_memory_consolidation\n\n输入:\n- user_id\n- recent_features\n\n输出:\n- consolidated_features\n- summary", "icons/memory.png")
            
            latent_intent = Custom("LATENT_INTENT\n_latent_intent_discovery\n\n输入:\n- message\n- conversation_history\n- existing_features\n\n输出:\n- latent_needs\n- behavior_predictions", "icons/latent.png")
            
            stability = Custom("STABILITY_EVALUATION\n_stability_evaluation\n\n输入:\n- features\n- feature_type\n- feature_value\n\n输出:\n- stability_period_days\n- decay_rate\n- change_likelihood", "icons/stability.png")
            
            profile_update = Custom("PROFILE_UPDATE\nprofile_update\n\n更新用户画像", "icons/update.png")
    
    # 任务状态
    with Cluster("任务状态枚举"):
        pending = Custom("PENDING\n等待中", "icons/pending.png")
        running = Custom("RUNNING\n运行中", "icons/running.png")
        completed = Custom("COMPLETED\n已完成", "icons/completed.png")
        failed = Custom("FAILED\n失败", "icons/failed.png")
    
    # 状态查询
    with Cluster("状态查询接口"):
        get_task_status = Custom("get_task_status(task_id)\n\n返回:\n- task_id\n- task_type\n- status\n- output_data\n- error\n- timestamps", "icons/query.png")
        
        get_user_tasks = Custom("get_user_tasks(user_id)\n\n返回用户所有任务列表", "icons/query.png")
    
    # LLM 调用
    llm = Custom("LLM Provider\n(Qwen/OpenAI)", "icons/llm.png")
    
    # 连接关系
    submit_task >> tasks_dict
    submit_task >> running_tasks
    submit_task >> max_concurrent
    max_concurrent >> schedule_logic
    schedule_logic >> run_task
    
    run_task >> deep_think
    run_task >> feature_corr
    run_task >> relationship
    run_task >> memory
    run_task >> latent_intent
    run_task >> stability
    run_task >> profile_update
    
    deep_think >> llm
    feature_corr >> llm
    relationship >> llm
    memory >> llm
    latent_intent >> llm
    stability >> llm
    
    run_task >> pending
    run_task >> running
    run_task >> completed
    run_task >> failed
    
    tasks_dict >> get_task_status
    tasks_dict >> get_user_tasks
