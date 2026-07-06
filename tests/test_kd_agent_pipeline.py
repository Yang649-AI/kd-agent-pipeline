from kd_agent.agent import answer_question
from kd_agent.build import build_index
from kd_agent.config import default_config
from kd_agent.evaluation import run_evaluation
from kd_agent.indexing import load_index


def test_build_search_and_evaluate():
    config = default_config()
    build_index(config)
    index = load_index(config.index_path)
    result = answer_question(index, "What is virtual memory?", top_k=5, context_tokens=600)
    assert result.retrieved
    assert result.citations
    assert "address" in result.answer.lower()

    metrics = run_evaluation(config)
    assert metrics["num_questions"] >= 6
    assert metrics["hit_at_5"] >= 0.8
    assert metrics["hallucination_rate_no_citation"] == 0
