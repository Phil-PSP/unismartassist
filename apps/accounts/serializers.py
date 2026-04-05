from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'user_id', 'email', 'first_name', 'last_name',
                  'full_name', 'role', 'phone', 'points', 'study_streak', 'avatar']
        read_only_fields = ['user_id', 'role', 'points', 'study_streak']

    def get_full_name(self, obj):
        return obj.get_full_name()
