import requests

# Login como usuario1
login_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                              json={'email': 'usuario1@techcorp.com', 'password': 'User123!'})

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Ver límites
    response = requests.get('http://localhost:8000/api/v1/chatbots/limits', headers=headers)
    if response.status_code == 200:
        limits = response.json()
        usage = limits['current_usage']
        print(f'Usuario1 tiene {usage["user_chatbots"]} chatbots de {usage["user_limit"]} permitidos')
        print(f'La empresa tiene {usage["company_chatbots"]} chatbots de {usage["company_limit"]} permitidos')
        print(f'Puede crear más: {limits["can_create_chatbot"]}')
        
        if usage['user_chatbots'] >= usage['user_limit']:
            print('✅ CORRECTO: El usuario ya alcanzó su límite personal')
        else:
            print('❌ ERROR: El usuario debería poder crear más')
