from django.db import models


class TrainingMode(models.Model):
    slug = models.SlugField("Код режиму", unique=True, choices=[
        ("reaction", "Швидкість реакції"),
        ("concentration", "Концентрація уваги"),
    ])
    name = models.CharField("Назва", max_length=100)
    description = models.TextField("Опис", max_length=500)
    is_active = models.BooleanField("Доступний", default=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Режим тренування"
        verbose_name_plural = "Режими тренування"

    def __str__(self):
        return self.name
