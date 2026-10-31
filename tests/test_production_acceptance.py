import unittest

from company.production_acceptance import (
    AgentRunRecord, DeliveryStage, can_perform_external_action,
    evaluate_delivery_transition, validate_video_delivery,
)


def proof(source="test-integration", reference="run-123"):
    return {"verified": True, "source": source, "reference": reference}


class ProductionAcceptanceTests(unittest.TestCase):
    def test_payment_claim_without_provider_proof_is_rejected(self):
        result = evaluate_delivery_transition(
            DeliveryStage.PAYMENT_VERIFIED,
            {
                "client_interest_record": "client said yes",
                "demo_scope_approval": True,
                "payment_provider_verification": "paid",
            },
        )
        self.assertFalse(result.allowed)
        self.assertIn("payment_provider_verification", result.required_evidence)

    def test_production_handover_requires_every_gate_and_owner_approval(self):
        evidence = {
            key: proof(reference=key)
            for key in (
                "payment_provider_verification", "production_build_passed",
                "security_checks_passed", "client_acceptance_checks_passed",
                "deployment_verified", "admin_access_verified", "handover_record",
            )
        }
        result = evaluate_delivery_transition(
            DeliveryStage.HANDED_OVER, evidence, owner_approved=True
        )
        self.assertTrue(result.allowed)

    def test_handover_without_owner_approval_is_rejected(self):
        evidence = {
            key: proof(reference=key)
            for key in (
                "payment_provider_verification", "production_build_passed",
                "security_checks_passed", "client_acceptance_checks_passed",
                "deployment_verified", "admin_access_verified", "handover_record",
            )
        }
        result = evaluate_delivery_transition(DeliveryStage.HANDED_OVER, evidence)
        self.assertFalse(result.allowed)
        self.assertIn("owner_approval", result.required_evidence)

    def test_agent_cannot_complete_without_output_and_evidence(self):
        run = AgentRunRecord(agent_id="harvey", task_id="task-1")
        with self.assertRaises(ValueError):
            run.transition("completed", output={"summary": "done"})
        with self.assertRaises(ValueError):
            run.transition("completed", output={"summary": "done"},
                           evidence=[{"source": "web"}])

    def test_agent_completion_with_traceable_evidence_is_allowed(self):
        run = AgentRunRecord(agent_id="harvey", task_id="task-1")
        run.transition("completed", output={"summary": "audit"},
                       evidence=[{"source": "public-site", "reference": "https://example.org"}])
        self.assertEqual(run.status, "completed")

    def test_social_action_is_default_denied(self):
        result = can_perform_external_action(
            "send_direct_message", connector_verified=False, owner_approved=True,
            platform_permission_verified=True,
        )
        self.assertFalse(result.allowed)

    def test_paid_ads_require_approved_budget(self):
        result = can_perform_external_action(
            "paid_promotion", connector_verified=True, owner_approved=True,
            budget_approved=False,
        )
        self.assertFalse(result.allowed)
        self.assertIn("budget_approval", result.required_evidence)

    def test_script_is_not_a_completed_video(self):
        result = validate_video_delivery({"script": "Hello world"})
        self.assertFalse(result.allowed)
        self.assertIn("rendered_asset_uri", result.required_evidence)

    def test_rendered_video_requires_all_quality_checks(self):
        manifest = {
            "rendered_asset_uri": "artifact://render/123.mp4",
            "duration_seconds": 30,
            "aspect_ratio": "9:16",
            "voiceover_qa": True,
            "audio_mix_qa": True,
            "caption_safe_area_qa": True,
            "pacing_qa": True,
            "claims_qa": True,
        }
        self.assertTrue(validate_video_delivery(manifest).allowed)


if __name__ == "__main__":
    unittest.main()
