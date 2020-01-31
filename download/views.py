import csv
import email.utils
from django.shortcuts import render
from django.shortcuts import render,  get_list_or_404, get_object_or_404
from registration.models import ScrapeTarget, ScrapeResult
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

class DownloadView(View):

    filename = 'scrape_results.csv'
    content_type = 'text/csv; charset=UTF-8'

    def get_filename(self):
        return self.filename

    def get_context_disposition(self):
        """ Get RFC 2231 formated Context Disposition """
        context_disposition = 'attachment; filename*='
        name = email.utils.encode_rfc2231(self.get_filename(), charset='UTF-8')
        return context_disposition + name

    def get(self, request, *args, **kwargs):
        target_id = self.kwargs['target_id']
        target = self.check_if_requester_owned_this(target_id)
        if target is None:
            return HttpResponseRedirect(reverse('accounts:login'))

        values = self.fetch_scrape_results(target)
        response = self.write_to_response(values)
        return response

    def check_if_requester_owned_this(self, target_id):
        '''
            args: target_id
            returns: if requester own this target, return instance of ScrapeTarget, else return None
        '''
        try:
            target = ScrapeTarget.objects.get(pk = target_id)
        except ObjectDoesNotExist:
            return None

        owner = target.owner
        requester = self.request.user
        if owner == requester:
            return target
        else:
            return None

    def fetch_scrape_results(self, target):
        '''
        Args:
            target: instance of ScrapeTarget
        Returns:
            list of values fetched from ScrapeResults
        '''
        results = ScrapeResult.objects.filter(target = target)
        values = [[result.time.strftime('%Y/%m/%d %H:%M'), result.value] for result in results]
        return values

    def write_to_response(self, values):
        response = HttpResponse(content_type=self.content_type)
        response['Content-Disposition'] = self.get_context_disposition()
        writer = csv.writer(response, quoting=csv.QUOTE_NONNUMERIC)
        for row in values:
            writer.writerow(row)
        return response
