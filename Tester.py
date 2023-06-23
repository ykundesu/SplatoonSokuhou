from atproto import Client

def main():
    client = Client()
    profile = client.login()
    print('Welcome,', profile.displayName)
    
    post_ref = client.send_post(text='プログラムからのテストだｿﾞー')
    client.like(post_ref)

    
if __name__ == '__main__':
    main()
