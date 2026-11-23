from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from pymongo.errors import ServerSelectionTimeoutError

from .analytics import analyze_results


class ApplicationTests(TestCase):
    def setUp(self):
        mongo = patch("training.mongo.MongoClient", side_effect=AssertionError("MongoDB is not allowed in tests"))
        mongo.start()
        self.addCleanup(mongo.stop)
        self.user = User.objects.create_user(username="testuser", password="Test-pass-12345")

    def test_registration(self):
        response = self.client.post(reverse("users:register"), {
            "first_name": "Іван",
            "last_name": "Іваненко",
            "username": "newuser",
            "password1": "Test-pass-67890",
            "password2": "Test-pass-67890",
        })

        self.assertRedirects(response, reverse("users:profile"), fetch_redirect_response=False)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.first_name, "Іван")
        self.assertTrue(user.check_password("Test-pass-67890"))

    def test_invalid_registration(self):
        response = self.client.post(reverse("users:register"), {
            "first_name": "Іван",
            "last_name": "Іваненко",
            "username": "newuser",
            "password1": "Test-pass-67890",
            "password2": "Different-pass-67890",
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
        self.assertEqual(response.context["form"].errors.as_data()["password2"][0].code, "password_mismatch")
        self.assertContains(response, response.context["form"].errors["password2"][0])

    @patch("users.views.get_collection")
    def test_profile_requires_login(self, get_collection):
        profile_url = reverse("users:profile")
        response = self.client.get(profile_url)
        self.assertRedirects(
            response, f"{reverse('users:login')}?next={profile_url}",
            fetch_redirect_response=False,
        )
        get_collection.assert_not_called()

        self.assertTrue(self.client.login(username="testuser", password="Test-pass-12345"))
        get_collection.return_value.find.return_value.sort.return_value.limit.return_value = []
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], self.user)
        get_collection.return_value.find.assert_called_once_with({"user_id": self.user.id})

    @patch("training.views.get_collection")
    def test_save_reaction_result(self, get_collection):
        self.client.force_login(self.user)
        attempt_id = "12345678-1234-4234-8234-123456789abc"
        now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
        with patch("training.views.timezone.now", return_value=now):
            response = self.client.post(reverse("training:save_result"), {
                "mode": "reaction",
                "reaction_time_ms": 300,
                "attempt_id": attempt_id,
                "user_id": self.user.id + 1,
            }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"saved": True})
        get_collection.return_value.insert_one.assert_called_once_with({
            "user_id": self.user.id,
            "mode": "reaction",
            "created_at": now,
            "attempt_id": attempt_id,
            "reaction_time_ms": 300,
        })

    def test_reaction_analysis(self):
        now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
        documents = [
            {
                "mode": "reaction",
                "created_at": now - timedelta(minutes=5 - index),
                "reaction_time_ms": value,
            }
            for index, value in enumerate([400, 350, 300, 250, 200])
        ]

        result = analyze_results(documents, "day", now)
        self.assertEqual(result["reaction"]["count"], 5)
        self.assertEqual(result["reaction"]["mean"], 300)
        self.assertEqual(result["reaction"]["best"], 200)
        self.assertEqual(result["reaction"]["worst"], 400)
        self.assertAlmostEqual(result["trend"]["slope"], -50)
        self.assertEqual(result["trend"]["message"], "Час реакції має тенденцію до зменшення.")

    @patch("training.views.get_collection")
    def test_statistics_only_for_current_user(self, get_collection):
        other_user = User.objects.create_user(username="otheruser", password="Test-pass-12345")
        now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
        documents = [
            {"user_id": self.user.id, "mode": "reaction", "created_at": now, "reaction_time_ms": 321},
            {"user_id": other_user.id, "mode": "reaction", "created_at": now, "reaction_time_ms": 654},
        ]
        collection = get_collection.return_value
        collection.find.side_effect = lambda query, projection: [
            document for document in documents if document["user_id"] == query.get("user_id")
        ]

        for user, expected_time in [(self.user, 321), (other_user, 654)]:
            self.client.force_login(user)
            with patch("training.views.timezone.now", return_value=now):
                response = self.client.get(reverse("training:statistics"), {"period": "day"})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(collection.find.call_args.args[0]["user_id"], user.id)
            self.assertEqual(response.context["reaction"]["count"], 1)
            self.assertEqual(response.context["reaction"]["mean"], expected_time)

        self.assertEqual(collection.find.call_count, 2)

    @patch("training.views.get_collection")
    def test_invalid_reaction_result_is_not_saved(self, get_collection):
        self.client.force_login(self.user)
        response = self.client.post(reverse("training:save_result"), {
            "mode": "reaction",
            "reaction_time_ms": -100,
            "attempt_id": "12345678-1234-4234-8234-123456789abc",
        }, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Некоректний результат тренування.")
        get_collection.assert_not_called()

    @patch("training.views.get_collection")
    def test_save_concentration_result(self, get_collection):
        self.client.force_login(self.user)
        now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
        attempt_id = "12345678-1234-4234-8234-123456789abc"
        with patch("training.views.timezone.now", return_value=now):
            response = self.client.post(reverse("training:save_result"), {
                "mode": "concentration",
                "correct_answers": 7,
                "wrong_answers": 1,
                "missed_signals": 2,
                "attempt_id": attempt_id,
            }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"saved": True})
        get_collection.return_value.insert_one.assert_called_once_with({
            "user_id": self.user.id,
            "mode": "concentration",
            "created_at": now,
            "attempt_id": attempt_id,
            "correct_answers": 7,
            "wrong_answers": 1,
            "missed_signals": 2,
        })

    @patch("training.views.get_collection", side_effect=ServerSelectionTimeoutError("connection failed"))
    def test_statistics_when_mongodb_unavailable(self, get_collection):
        self.client.force_login(self.user)
        response = self.client.get(reverse("training:statistics"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Не вдалося завантажити статистику")
        self.assertNotContains(response, "connection failed")
        get_collection.assert_called_once()

    @patch("training.analytics.LinearRegression")
    def test_trend_requires_five_results(self, regression):
        now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
        documents = [
            {"mode": "reaction", "created_at": now - timedelta(minutes=index), "reaction_time_ms": 300}
            for index in range(4)
        ]

        result = analyze_results(documents, "day", now)
        self.assertEqual(result["reaction"]["count"], 4)
        self.assertIsNone(result["trend"]["slope"])
        self.assertEqual(result["trend"]["message"], "Недостатньо даних для аналізу тенденції")
        regression.assert_not_called()
