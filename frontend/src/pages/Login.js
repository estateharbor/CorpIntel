import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Building2, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const { login, register, demoLogin, googleLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const dest = location.state?.from || "/dashboard";
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", name: "" });

  const upd = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const doLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(form.email, form.password);
      toast.success("Welcome back!");
      navigate(dest, { replace: true });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const doRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form.email, form.password, form.name);
      toast.success("Account created!");
      navigate(dest, { replace: true });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const doDemo = async () => {
    setLoading(true);
    try {
      await demoLogin();
      toast.success("Logged in as Demo (Pro)");
      navigate(dest, { replace: true });
    } catch (err) {
      toast.error("Demo login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2.5 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Building2 className="h-5 w-5" />
          </div>
          <span className="font-heading font-bold text-xl">CorpIntel India</span>
        </Link>
        <Card className="p-6">
          <Tabs defaultValue="login">
            <TabsList className="grid grid-cols-2 w-full">
              <TabsTrigger value="login" data-testid="login-tab">Sign in</TabsTrigger>
              <TabsTrigger value="register" data-testid="register-tab">Create account</TabsTrigger>
            </TabsList>
            <TabsContent value="login">
              <form onSubmit={doLogin} className="space-y-4 mt-4">
                <div className="space-y-1.5">
                  <Label>Email</Label>
                  <Input type="email" required value={form.email} onChange={upd("email")} placeholder="you@company.com" data-testid="login-email" />
                </div>
                <div className="space-y-1.5">
                  <Label>Password</Label>
                  <Input type="password" required value={form.password} onChange={upd("password")} placeholder="••••••••" data-testid="login-password" />
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="login-submit">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sign in"}
                </Button>
              </form>
            </TabsContent>
            <TabsContent value="register">
              <form onSubmit={doRegister} className="space-y-4 mt-4">
                <div className="space-y-1.5">
                  <Label>Full name</Label>
                  <Input required value={form.name} onChange={upd("name")} placeholder="Your name" data-testid="register-name" />
                </div>
                <div className="space-y-1.5">
                  <Label>Email</Label>
                  <Input type="email" required value={form.email} onChange={upd("email")} placeholder="you@company.com" data-testid="register-email" />
                </div>
                <div className="space-y-1.5">
                  <Label>Password</Label>
                  <Input type="password" required value={form.password} onChange={upd("password")} placeholder="Min 6 characters" data-testid="register-password" />
                </div>
                <Button type="submit" className="w-full" disabled={loading} data-testid="register-submit">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Create account"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
            <div className="relative flex justify-center text-xs"><span className="bg-card px-2 text-muted-foreground">or</span></div>
          </div>

          <Button variant="outline" className="w-full" onClick={googleLogin} data-testid="login-google">
            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Continue with Google
          </Button>

          <Button variant="ghost" className="w-full mt-2 text-accent" onClick={doDemo} disabled={loading} data-testid="login-demo">
            <Sparkles className="mr-2 h-4 w-4" /> Try the Demo (Pro access)
          </Button>
        </Card>
        <p className="text-center text-xs text-muted-foreground mt-4">
          By continuing you agree to our terms. <Link to="/" className="underline">Back to home</Link>
        </p>
      </div>
    </div>
  );
}
