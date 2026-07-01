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
  const { login, register, demoLogin } = useAuth();
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

          <Button variant="ghost" className="w-full text-accent" onClick={doDemo} disabled={loading} data-testid="login-demo">
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
