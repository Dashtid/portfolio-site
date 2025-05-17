 from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = [
            {
                'name': 'Portfolio',
                'description': 'View my project portfolio',
                'url': '/portfolio/',  # This can be a subpath or an external URL
                'icon': 'folder',
            },
            {
                'name': 'Blog',
                'description': 'Read my latest articles',
                'url': '/blog/',
                'icon': 'book',
            },
            {
                'name': 'Contact',
                'description': 'Get in touch with me',
                'url': '/contact/',
                'icon': 'envelope',
            },
            # Add more services as needed
        ]
        return context