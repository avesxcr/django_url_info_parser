import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, \
    PasswordResetCompleteView, PasswordChangeView, PasswordChangeDoneView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView
from data_parser.models import Link, Collection
from django.http import Http404, JsonResponse
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .forms import RegisterForm, LinkForm, ParseUrlForm, CollectionForm
from parser import UrlParser
import asyncio


@api_view(['GET'])
@swagger_auto_schema(
    operation_description="Returns a list of all users.",
    responses={200: 'OK'})


@login_required
def profile_view(request):
    current_user = request.user

    all_collections = Collection.objects.all()

    collections_with_links = []
    all_links_count = Link.objects.filter(user=current_user).count()

    for collection in all_collections:
        links_count = Link.objects.filter(user=current_user, collection_id=collection.id).count()
        if links_count > 0:
            collections_with_links.append({
                'collection': collection,
            })

    context = {
        'collections_count': len(collections_with_links),
        'links_count': all_links_count
    }

    return render(request, context=context, template_name='profile.html')


class RegisterView(FormView):
    model = User
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('data_parser:profile')

    @swagger_auto_schema(
        operation_description="Process registration form.",
        responses={200: 'OK'}
    )

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class WebPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email_.html'
    html_email_template_name = 'registration/password_reset_email_.html'
    success_url = reverse_lazy('data_parser:password_reset_done')


class WebPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm_.html'
    success_url = reverse_lazy('data_parser:password_reset_complete')


class WebPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete_.html'


class WebPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done_.html'


class WebPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_.html'
    success_url = reverse_lazy('data_parser:password_change_done')


class WebPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'registration/password_change_done_.html'

@api_view(['GET'])
@swagger_auto_schema(
    operation_description="View user's URLs.",
    responses={200: 'OK'}
)

@login_required
def urls_view(request):
    current_user = request.user

    links = Link.objects.filter(user=current_user)

    context = {
        'links': links
    }

    return render(request, 'view_urls.html', context)

@api_view(['GET', 'POST'])
@swagger_auto_schema(
    operation_description="Edit link details.",
    responses={200: 'OK'}
)

@login_required
def edit_link(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    if request.method == 'POST':
        form = LinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            return redirect('data_parser:view_links')
    else:
        form = LinkForm(instance=link)
    return render(request, 'edit_link.html', {'form': form})


@api_view(['GET'])
@swagger_auto_schema(
    operation_description="View details of a specific link.",
    responses={200: 'OK'}
)
@login_required
def view_link(request, link_id):
    link = get_object_or_404(Link, id=link_id)
    return render(request, 'view_link.html', {'link': link})

@api_view(['GET', 'POST'])
@swagger_auto_schema(
    operation_description="Add a new link.",
    responses={200: 'OK'}
)

@login_required
def add_link(request):
    if request.method == 'POST':
        form = LinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.user = request.user
            link.save()
            return redirect('data_parser:view_links')
    else:
        form = LinkForm()
    return render(request, 'add_link.html', {'form': form})


@api_view(['GET'])
@swagger_auto_schema(
    operation_description="Delete all links.",
    responses={200: 'OK'}
)
@login_required
def delete_all_links(request):
    if Link.objects.filter(user=request.user).exists():
        Link.objects.filter(user=request.user).delete()
    return redirect(reverse_lazy('data_parser:view_links'))


@api_view(['GET'])
@swagger_auto_schema(
    operation_description="Delete selected links.",
    responses={200: 'OK'}
)
@login_required
def delete_selected_links(request):
    if request.method == 'GET':
        selected_ids = request.GET.getlist('ids')
        selected_ids = [int(id) for ids in selected_ids for id in ids.split(',') if id.isdigit()]
        if selected_ids:
            if Link.objects.filter(user=request.user, id__in=selected_ids).exists():
                Link.objects.filter(user=request.user, id__in=selected_ids).delete()
        return redirect(reverse_lazy('data_parser:view_links'))
    return redirect(reverse_lazy('data_parser:view_links'))


@api_view(['POST'])
@swagger_auto_schema(
    operation_description="Parse URLs and save links.",
    request_body=LinkForm,
    responses={200: 'OK'})

@login_required
def url_parser(request):
    if request.method == 'POST':
        form = ParseUrlForm(request.POST)
        if form.is_valid():
            urls = form.cleaned_data['url']
            asyncio.run(parse_info_async(urls, request.user))
            return redirect(reverse_lazy('data_parser:view_links'))
    else:
        form = ParseUrlForm()
    return render(request, 'urls_parser.html', {'form': form})


@api_view(['GET'])
@swagger_auto_schema(
    operation_description="Parse URLs and save links.",
    responses={200: 'OK'}
)
@login_required
def url_parser_by_link(request, url):
    if request.method == 'GET':
        result = asyncio.run(parse_info_async(url, request.user, get_=True))
        return JsonResponse(json.loads(result))


async def parse_info_async(urls, user, get_=None):
    parse_info = UrlParser()
    result = await parse_info.parse_info(urls, user, get_)
    return result

@api_view(['GET'])
@swagger_auto_schema(
    operation_description="View user collections.",
    responses={200: 'OK'}
)

@login_required
def view_collections(request):
    current_user = request.user

    all_collections = Collection.objects.filter(user=current_user)

    collections_with_links = []
    for collection in all_collections:
        links_count = Link.objects.filter(user=current_user, collection_id=collection.id).count()
        if links_count > 0:
            collections_with_links.append({
                'collection': collection,
                'links_count': links_count
            })

    context = {
        'collections_with_links': collections_with_links
    }

    return render(request, 'view_collections.html', context)


@api_view(['GET'])
@swagger_auto_schema(
    operation_description="View collection details.",
    responses={200: 'OK'}
)

@login_required
def view_collection(request, collection_name):
    current_user = request.user

    collection = get_object_or_404(Collection, name=collection_name, user=current_user)
    links = Link.objects.filter(user=current_user, collection=collection)

    if not links:
        raise Http404("No links found in this collection.")

    context = {
        'collection': collection,
        'links': links
    }

    return render(request, 'view_collection.html', context)

@api_view(['POST'])
@swagger_auto_schema(
    operation_description="Delete all collections.",
    responses={200: 'OK'}
)
@login_required
def delete_all_collections(request):
    Collection.objects.filter(user=request.user).delete()
    return redirect(reverse_lazy('data_parser:view_collections'))


@api_view(['GET', 'POST'])
@swagger_auto_schema(
    operation_description="Delete selected collections.",
    responses={200: 'OK'}
)
@login_required
def delete_selected_collections(request):
    if request.method == 'GET':
        selected_ids = request.GET.getlist('ids')
        selected_ids = [int(id) for id in selected_ids if id.isdigit()]
        Collection.objects.filter(id__in=selected_ids, user=request.user).delete()
    return redirect(reverse_lazy('data_parser:view_collections'))

@api_view(['GET', 'POST'])
@swagger_auto_schema(
    operation_description="Edit collection details.",
    responses={200: 'OK'}
)

@login_required
def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id, user=request.user)
    if request.method == 'POST':
        form = CollectionForm(request.POST, instance=collection)
        if form.is_valid():
            form.save()
            return redirect('data_parser:view_collections')
    else:
        form = CollectionForm(instance=collection)
    return render(request, 'edit_collection.html', {'form': form})

@api_view(['GET'])
@swagger_auto_schema(
    operation_description="View top users.",
    responses={200: 'OK'}
)

@login_required
def view_top_users(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT DISTINCT id, name FROM data_parser_collection;')
        categories = cursor.fetchall()

        count_expressions = []
        for category in categories:
            category_id = category[0]
            category_name = category[1]
            count_expression = f'COUNT(CASE WHEN c.id = {category_id} THEN l.id ELSE NULL END) AS {category_name}_links'
            count_expressions.append(count_expression)

        count_columns = ', '.join(count_expressions)

        dynamic_query = f'''
            SELECT u.id, u.username,
            {count_columns},
            COUNT(l.id) AS total_links,
            MAX(u.date_joined) AS registration_date
            FROM auth_user AS u
            LEFT JOIN data_parser_link AS l ON u.id = l.user_id
            LEFT JOIN data_parser_collection AS c ON l.collection_id = c.id
            GROUP BY u.id, u.username
            ORDER BY total_links DESC, registration_date
            LIMIT 10;
        '''

        try:
            cursor.execute(dynamic_query)
            rows = cursor.fetchall()

            formatted_rows = []
            for row in rows:
                user_data = row[:2]
                category_data = {}
                for i, category in enumerate(categories):
                    category_name = category[1]
                    category_count = row[i + 2] if i + 2 < len(row) else 0
                    category_data[category_name] = category_count
                total_links = row[-2]
                registration_date = row[-1]
                formatted_row = user_data + (category_data, total_links, registration_date)
                formatted_rows.append(formatted_row)

            categories = [category[1] for category in categories]

            context = {
                'rows': formatted_rows,
                'categories': categories
            }
        except Exception as e:
            context = {
                'error_message': str(e)
            }

        return render(request, 'view_users.html', context)