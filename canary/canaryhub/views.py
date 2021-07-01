from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
import requests
import json

CLIENT_ID = 'c9e0b4597188c64ad089'
CLIENT_SECRET = '4ba097d2c9b6671592e1bf2c5c6a23b6b9cddacf'

def index(request):
    users = User.objects.all()
    for user in users:
        user.delete()
    return render(request, 'index.html')

def link_github(request):
    name = request.GET.get('name')
    first_name, last_name = name.split()
    username = request.GET.get('username')
    pword = request.GET.get('password') # not safe storage here
    user = User.objects.create_user(username, password=pword, first_name=first_name, last_name=last_name)
    login(request, user)
    return render(request, 'github_link.html')

def get_github_authentication(request):
    github_code = request.GET.get('code', None)
    if not github_code and 'access_token' not in request.session:
        return redirect(f'https://github.com/login/oauth/authorize?' +
                        f'client_id={CLIENT_ID}&' +
                        f'redirect_url=localhost:8000{reverse("canary_hub")}&' +
                        f'scope=admin:repo_hook public_repo repo write:repo_hook'
                        )
    
    res2 = requests.post(f'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        params={'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'code' : github_code})
    token = (res2.json()).get('access_token', '')
    if 'access_token' not in request.session or token != request.session['access_token']:
        request.session['access_token'] = token
            
    return redirect(reverse('repositories'))

def repositories(request):
    repos_res = requests.get(f"https://api.github.com/user/repos",
        headers={'Authorization': f'token {request.session["access_token"]}'},
        params={'accept': 'application/vnd.github.v3+json'})
    return render(request, 'repos.html', {'repos': repos_res.json()})

def set_up_webhooks(request):
    owner_repo = request.GET.get('full_name', '')

    import pdb; pdb.set_trace()

    request.session['owner_repo'] = owner_repo
    request.session['selected_repo'] = owner_repo.split('/')[-1]
    
    webhook_res = requests.post(f"https://api.github.com/repos/{owner_repo}/hooks",
        headers={
            'Authorization': f'token {request.session["access_token"]}',
            'content_type': 'application/json',
            'accept': 'application/vnd.github.v3+json'},
        data=json.dumps({
            'events': ['push', 'pull_request'],
            'config': {
                'url': 'http://d625a58bff86.ngrok.io' + reverse('handle_webhook'),
                'content_type': 'json'
            }
        }))
    import pdb; pdb.set_trace()
    return redirect(reverse('repo_events'))

@csrf_exempt
def handle_webhook(request):
    import pdb; pdb.set_trace()
    if request.body == b'':
        return
    data = json.loads(request.body)
    request.session['repo_events'][request.session['selected_repo']].append(data)
    

def view_webhook_events(request):
    import pdb; pdb.set_trace()
    if 'repo_events' in request.session:
        if request.session['selected_repo'] in request.session['repo_events']: 
            data = request.session['repo_events'][request.session['selected_repo']]
    else:
        # below request will only gather the first page containing 30 events max
        events = requests.get(f'https://api.github.com/repos/{request.session["owner_repo"]}/events',
                              headers={'Authorization': f'token {request.session["access_token"]}'},
                              params={'Accept': 'application/vnd.github.v3+json'},)
        import pdb; pdb.set_trace()
        data = events.json()
        request.session['repo_events'] = {request.session['selected_repo']: data}
        
    return render(request, 'repo_events.html', {'events': data})