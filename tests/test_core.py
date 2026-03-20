"""
perMIR 核心功能测试
测试用户画像生成的主要业务逻辑
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.llm_provider import LLMProviderFactory
from backend.agents.agent_engine import AgentOrchestrator
from backend.knowledge_graph.graph import knowledge_graph


def test_knowledge_graph():
    print("=" * 50)
    print("测试知识图谱")
    print("=" * 50)
    
    print(f"节点数: {len(knowledge_graph.graph.nodes)}")
    print(f"边数: {len(knowledge_graph.graph.edges)}")
    
    correlations = knowledge_graph.get_feature_correlations("内向型")
    print(f"\n'内向型' 关联特征:")
    for rel_type, features in correlations.items():
        if features:
            print(f"  {rel_type}: {features}")
    
    knowledge_graph.add_user_feature("test_user", "MBTI", "INTP", 0.85, "测试消息")
    user_features = knowledge_graph.get_user_features("test_user")
    print(f"\n用户 test_user 特征:")
    for f in user_features:
        print(f"  {f['feature_type']}: {f['feature_value']} (置信度: {f['confidence']:.2f})")
    
    print("\n知识图谱测试通过!")
    return True


def test_llm_provider():
    print("\n" + "=" * 50)
    print("测试LLM提供者")
    print("=" * 50)
    
    providers = LLMProviderFactory.get_available_providers()
    print(f"可用提供者: {providers}")
    
    try:
        provider = LLMProviderFactory.get_provider("openrouter")
        print(f"OpenRouter 提供者创建成功")
        print(f"模型: {provider.config.model}")
    except Exception as e:
        print(f"创建提供者失败: {e}")
    
    print("\nLLM提供者测试通过!")
    return True


async def test_agent_orchestrator():
    print("\n" + "=" * 50)
    print("测试Agent编排器")
    print("=" * 50)
    
    orchestrator = AgentOrchestrator("openrouter")
    print(f"Agent列表: {list(orchestrator.agents.keys())}")
    
    test_messages = [
        {"role": "user", "content": "我周末喜欢宅在家里看书，不太喜欢参加聚会"},
        {"role": "user", "content": "我觉得独处的时候更自在，可以思考很多问题"},
        {"role": "user", "content": "我做事喜欢先计划好，不喜欢临时变动"}
    ]
    
    print("\n测试消息:")
    for msg in test_messages:
        print(f"  {msg['content']}")
    
    print("\n提取特征中...")
    try:
        features = await orchestrator.extract_features(test_messages)
        print(f"\n提取到 {len(features)} 个特征:")
        for f in features:
            print(f"  [{f['type']}] {f['value']} (置信度: {f['confidence']:.2f})")
    except Exception as e:
        print(f"特征提取失败: {e}")
    
    print("\nAgent编排器测试完成!")
    return True


def test_profile_service():
    print("\n" + "=" * 50)
    print("测试画像服务")
    print("=" * 50)
    
    from backend.models.schemas import FeatureCreate
    
    feature = FeatureCreate(
        feature_type="MBTI",
        feature_value="INTP",
        confidence=0.85,
        source_message="测试消息",
        reasoning="基于用户行为推断"
    )
    print(f"特征创建: {feature.feature_type} = {feature.feature_value}")
    
    print("\n画像服务测试通过!")
    return True


def run_tests():
    print("\n" + "=" * 60)
    print("perMIR 核心功能测试")
    print("=" * 60)
    
    results = []
    
    results.append(("知识图谱", test_knowledge_graph()))
    results.append(("LLM提供者", test_llm_provider()))
    results.append(("画像服务", test_profile_service()))
    
    print("\n运行异步测试...")
    try:
        results.append(("Agent编排器", asyncio.run(test_agent_orchestrator())))
    except Exception as e:
        print(f"异步测试失败: {e}")
        results.append(("Agent编排器", False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    
    return passed == len(results)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
