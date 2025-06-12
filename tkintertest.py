import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class LoginSignUpApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Login / Signup")
        self.geometry("350x250")

        self.result = None  # this will hold the returned data

        self.welcome = WelcomeScreen(self, self.show_login, self.show_signup)
        self.login = LoginScreen(self, self.handle_login, self.show_welcome)
        self.signup = SignupScreen(self, self.handle_signup, self.show_welcome)

        for screen in (self.welcome, self.login, self.signup):
            screen.grid(row=0, column=0, sticky="nsew")

        self.show_welcome()

    def run(self):
        self.mainloop()
        return self.result  # returned after self.quit()

    def show_welcome(self):
        self.welcome.tkraise()

    def show_login(self):
        self.login.tkraise()

    def show_signup(self):
        self.signup.tkraise()

    def handle_login(self, username, password):
        self.result = {"action": "login", "username": username, "password": password}
        self.quit()  # exit mainloop

    def handle_signup(self, username, password):
        self.result = {
            "action": "signup",
            "username": username,
            "password": password
        }
        self.quit()  # exit mainloop

    def close_app(self):
        self.destroy()  # This closes the GUI window

class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, master, login_callback, signup_callback):
        super().__init__(master)
        ctk.CTkLabel(self, text="Welcome!", font=ctk.CTkFont(size=20)).pack(pady=20)
        ctk.CTkButton(self, text="Login", command=login_callback).pack(pady=10)
        ctk.CTkButton(self, text="Signup", command=signup_callback).pack(pady=10)


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, submit_callback, back_callback):
        super().__init__(master)
        self.submit_callback = submit_callback

        ctk.CTkLabel(self, text="Login", font=ctk.CTkFont(size=18)).pack(pady=10)
        self.username = ctk.CTkEntry(self, placeholder_text="Username")
        self.username.pack(pady=5)
        self.password = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password.pack(pady=5)

        ctk.CTkButton(self, text="Submit", command=self.submit).pack(pady=5)
        ctk.CTkButton(self, text="Back", command=back_callback).pack()

    def submit(self):
        self.submit_callback(self.username.get(), self.password.get())


class SignupScreen(ctk.CTkFrame):
    def __init__(self, master, submit_callback, back_callback):
        super().__init__(master)
        self.submit_callback = submit_callback

        ctk.CTkLabel(self, text="Signup", font=ctk.CTkFont(size=18)).pack(pady=10)
        self.username = ctk.CTkEntry(self, placeholder_text="Username")
        self.username.pack(pady=5)
        self.password = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password.pack(pady=5)

        ctk.CTkButton(self, text="Submit", command=self.submit).pack(pady=5)
        ctk.CTkButton(self, text="Back", command=back_callback).pack()

    def submit(self):
        self.submit_callback(
            self.username.get(),
            self.password.get()
        )

  

if __name__ == "__main__":
    app = LoginSignUpApp()
    result = app.run()  # waits until user submits and closes
    print("Final result from GUI:", result)
