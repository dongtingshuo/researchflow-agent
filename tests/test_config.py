import unittest

from config import Settings


class SettingsTests(unittest.TestCase):
    def test_external_content_requires_explicit_llm_opt_in(self):
        self.assertFalse(Settings(openai_api_key="configured").llm_enabled)
        self.assertTrue(
            Settings(
                openai_api_key="configured",
                allow_external_content_to_llm=True,
            ).llm_enabled
        )

    def test_cross_encoder_is_opt_in_by_default(self):
        self.assertFalse(Settings().enable_cross_encoder_reranker)


if __name__ == "__main__":
    unittest.main()
