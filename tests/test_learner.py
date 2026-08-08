from app.learner import LearnerProgress


def test_weak_concept_detection_tracks_low_mastery():
    progress = LearnerProgress()
    progress.add_score(0.3, concept="Sea level rise")
    progress.add_score(0.5, concept="Sea level rise")
    progress.add_score(0.9, concept="Greenhouse gas inventory")

    weak = progress.weak_concepts

    assert weak[0]["concept"] == "Sea level rise"
    assert weak[0]["attempts"] == 2
    assert weak[0]["mastery"] == 0.4


def test_next_difficulty_uses_recent_mastery():
    progress = LearnerProgress()
    progress.add_score(0.9, concept="Climate")
    progress.add_score(0.9, concept="Climate")

    assert progress.next_difficulty == "advanced"
