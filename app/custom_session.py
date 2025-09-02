from flask.sessions import SecureCookieSessionInterface

class CustomSessionInterface(SecureCookieSessionInterface):
    """Custom session interface that doesn't use the 'partitioned' parameter."""
    
    def save_session(self, app, session, response):
        """Save the session without using the 'partitioned' parameter."""
        name = self.get_cookie_name(app)
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        secure = self.get_cookie_secure(app)
        samesite = self.get_cookie_samesite(app)
        httponly = self.get_cookie_httponly(app)
        
        # Add a "Vary: Cookie" header if the session was accessed at all.
        if session.accessed:
            response.vary.add("Cookie")
            
        # If the session is modified to be empty, remove the cookie.
        # If the session is empty, return without setting the cookie.
        if not session:
            if session.modified:
                response.delete_cookie(
                    name,
                    domain=domain,
                    path=path,
                    secure=secure,
                    samesite=samesite,
                    httponly=httponly,
                )
                response.vary.add("Cookie")
                
            return
            
        if not self.should_set_cookie(app, session):
            return
            
        expires = self.get_expiration_time(app, session)
        val = self.get_signing_serializer(app).dumps(dict(session))
        response.set_cookie(
            name,
            val,
            expires=expires,
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure,
            samesite=samesite,
        )
        response.vary.add("Cookie")