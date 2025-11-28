from base.choices import StateStatuses


class BaseDbIO:
    
    @property
    def model(self):
        raise NotImplementedError(
            "Subclasses must define the model property. "
            "Example: @property def model(self): return YourModel"
        )
    
    def get_obj(self, kwargs):
        return self.model.objects.get(**kwargs)
    
    def create_obj(self, kwargs):
        return self.model.objects.create(**kwargs)
    
    def update_obj(self, model_obj, kwargs):
        for key, value in kwargs.items():
            setattr(model_obj, key, value)
        model_obj.save()
        return model_obj
    
    def filter_obj(self, kwargs):
        queryset = self.model.objects.all()
        for key, value in kwargs.items():
            queryset = queryset.filter(**{key: value})
        return queryset
    
    def filter_active_obj(self, kwargs):
        queryset = self.model.objects.all()
        for key, value in kwargs.items():
            queryset = queryset.filter(**{key: value})
        queryset = queryset.filter(state=StateStatuses.ACTIVE)
        return queryset
    
    def get_all(self):
        return self.model.objects.all()
    
    def get_all_active(self):
        return self.model.objects.filter(state=StateStatuses.ACTIVE)
    
    def get_or_create_object(self, kwargs):
        return self.model.objects.get_or_create(**kwargs)
    
    def delete_obj(self, kwargs):
        obj = self.get_obj(kwargs)
        return obj.delete()
    
    def delete_with_filter_obj(self, kwargs):
        queryset = self.filter_obj(kwargs)
        return queryset.delete()
    
    def update_or_create(self, kwargs, defaults=None):
        if defaults is None:
            defaults = {}
        return self.model.objects.update_or_create(defaults=defaults, **kwargs)
