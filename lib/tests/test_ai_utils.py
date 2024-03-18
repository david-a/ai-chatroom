import unittest
from lib.ai_utils import (
    MAX_TOKENS_TO_GENERATE,
    MODEL_MAX_INPUT_TOKENS,
    MODEL_NAME,
    MODEL_TEMPERATURE,
    ai_call,
    limit_tokens,
    num_tokens_from_messages,
    wrap_system_message,
    to_openai_message,
)
from unittest import TestCase, mock
from lib.ai_utils import deserialize_message


class TestAIUtils(unittest.TestCase):
    def test_wrap_system_message(self):
        text = "Hello, World!"
        expected_result = {"role": "system", "content": "Hello, World!"}
        result = wrap_system_message(text)
        self.assertEqual(result, expected_result)

    def test_wrap_system_message_with_extra_spaces(self):
        text = "   Hello,    World!   "
        expected_result = {"role": "system", "content": "Hello, World!"}
        result = wrap_system_message(text)
        self.assertEqual(result, expected_result)

    def test_wrap_system_message_with_multiple_spaces(self):
        text = "Hello,     World!"
        expected_result = {"role": "system", "content": "Hello, World!"}
        result = wrap_system_message(text)
        self.assertEqual(result, expected_result)

    def test_to_openai_message_user_message(self):
        msg = "deddy:Hello, World!"
        self_name = "AI-12345"
        expected_result = {
            "role": "user",
            "content": "Hello, World!",
            "name": "deddy",
        }
        with mock.patch("lib.ai_utils.deserialize_message") as deserialize_message:
            deserialize_message.return_value = ["deddy", "Hello, World!"]

            result = to_openai_message(msg, self_name)
            self.assertEqual(result, expected_result)

    def test_to_openai_message_assistant_message(self):
        msg = "AI-12345:Hello, World!"
        self_name = "AI-12345"
        expected_result = {
            "role": "assistant",
            "content": "Hello, World!",
            "name": "AI-12345",
        }
        with mock.patch("lib.ai_utils.deserialize_message") as deserialize_message:
            deserialize_message.return_value = ["AI-12345", "Hello, World!"]

            result = to_openai_message(msg, self_name)
            self.assertEqual(result, expected_result)

    def test_num_tokens_from_messages_empty_list(self):
        messages = []
        expected_result = 2  # Only the assistant prompt tokens
        result = num_tokens_from_messages(messages)
        self.assertEqual(result, expected_result)

    def test_num_tokens_from_messages_single_message(self):
        messages = [{"role": "user", "content": "Hello, World!", "name": "deddy"}]
        expected_result = 12
        result = num_tokens_from_messages(messages)
        self.assertEqual(result, expected_result)

    def test_num_tokens_from_messages_multiple_messages(self):
        messages = [
            {"role": "user", "content": "Hello, World!", "name": "deddy"},
            {"role": "assistant", "content": "Hi there!", "name": "AI-12345"},
        ]
        expected_result = 23
        result = num_tokens_from_messages(messages)
        self.assertEqual(result, expected_result)

    def test_num_tokens_from_messages_with_different_model(self):
        messages = [{"role": "user", "content": "Hello, World!", "name": "deddy"}]
        model = "gpt-4"
        expected_result = 12
        result = num_tokens_from_messages(messages, model=model)
        self.assertEqual(result, expected_result)

    def test_limit_tokens_with_small_max_tokens(self):
        messages = [
            {"role": "user", "content": "Hello, World!", "name": "deddy"},
            {"role": "assistant", "content": "Hi there!", "name": "AI-12345"},
        ]
        system_message = {"role": "system", "content": "System message"}
        max_tokens = 20
        expected_result = [
            {"role": "assistant", "content": "Hi there!", "name": "AI-12345"}
        ]
        result = limit_tokens(messages, system_message, max_tokens)
        self.assertEqual(result, expected_result)

    @mock.patch("lib.ai_utils.wrap_system_message")
    @mock.patch("lib.ai_utils.limit_tokens")
    @mock.patch("lib.ai_utils.get_openai_client")
    def test_ai_call(
        self, mock_get_openai_client, mock_limit_tokens, mock_wrap_system_message
    ):
        conversation = [
            "user: Hello",
            "AI: Hi there!",
            "user: How are you?",
        ]
        system_prompt = "System prompt"
        bot_name = "AI"
        expected_result = "AI model response"

        mock_wrap_system_message.return_value = {
            "role": "system",
            "content": system_prompt,
        }
        mock_limit_tokens.return_value = [
            {"role": "user", "content": "Hello", "name": "user"},
            {"role": "assistant", "content": "Hi there!", "name": "AI"},
            {"role": "user", "content": "How are you?", "name": "user"},
        ]
        response_mock = mock.Mock(
            choices=[mock.Mock(message=mock.Mock(content=expected_result))]
        )
        mock_get_openai_client.return_value.chat.completions.create.return_value = (
            response_mock
        )

        result = ai_call(conversation, system_prompt, bot_name)
        self.assertEqual(result, expected_result)
        mock_wrap_system_message.assert_called_once_with(system_prompt)
        mock_limit_tokens.assert_called_once_with(
            [
                {"role": "user", "content": "Hello", "name": "user"},
                {"role": "assistant", "content": "Hi there!", "name": "AI"},
                {"role": "user", "content": "How are you?", "name": "user"},
            ],
            {"role": "system", "content": system_prompt},
            MODEL_MAX_INPUT_TOKENS,
        )
        mock_get_openai_client.return_value.chat.completions.create.assert_called_once_with(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hello", "name": "user"},
                {"role": "assistant", "content": "Hi there!", "name": "AI"},
                {"role": "user", "content": "How are you?", "name": "user"},
            ],
            temperature=MODEL_TEMPERATURE,
            max_tokens=MAX_TOKENS_TO_GENERATE,
        )


if __name__ == "__main__":
    unittest.main()
