from django.shortcuts import render,  get_list_or_404, get_object_or_404
from .models import ScrapeResult,ScrapeTarget
from django.views.generic import ListView, RedirectView, DetailView, CreateView, UpdateView
from .forms import ScrapeTargetForm
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class IndexView(RedirectView):
    url = '/targets'

class ScrapeTargetListView(ListView):
#    model = ScrapeTarget
#    queryset = ScrapeTarget.objects.all()
#    queryset = ScrapeTarget.objects.filter(owner=1)

    def get_queryset(self):
        user_id = self.request.user.id
        print("user_id:",user_id)
        return  ScrapeTarget.objects.filter(owner=user_id)

    # def scrapetarget_list_view(request):
    #     print("Enter scrapetarget_list_view() ")
    #     targets = get_list_or_404(ScrapeTarget, pk=request.user.id)
    #     print('ScrapeTargetListView',request.user.id)
    #     badSyntax
    #     return render(request, 'registration/scrapetarget_list.html', context={'targets': targets, 'test':'this is test'})

class ScrapeResultListView(ListView):
    model = ScrapeResult

    def get_queryset(self):
        target_id = self.kwargs.get('target_id',100)
        print("target_id:", target_id)
        return ScrapeResult.objects.filter(target=target_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_id"] = self.kwargs.get('target_id',100)
        return context

class ScrapeTargetCreateView(LoginRequiredMixin, CreateView):
    model = ScrapeTarget
    form_class = ScrapeTargetForm
    success_url = "/registration/"

    def get_initial(self):
        from django.contrib.auth import get_user
        owner = get_user(self.request)
        # print(f'get_initial() {self.request.user.id=}')
        print(f'get_initial() {owner.id=}') # DEBUG
        # return {'owner': owner, 'owner_id':self.request.user.id}
        return {'owner': owner}

class ScrapeTargetUpdateView(UpdateView):
    model = ScrapeTarget
    form_class = ScrapeTargetForm
    success_url = "/registration/"
