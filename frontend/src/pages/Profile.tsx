import React from "react";
import MarkdownEditor from "@/components/ui/MarkdownEditor";
import { Button } from "@/components/ui/button";
import Modal from "@/components/ui/modal";
import api from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Profile() {
  const { user, loading } = useAuth();
  const [bio, setBio] = React.useState<string>("");
  const [bioVisibility, setBioVisibility] = React.useState<"private" | "public">("private");
  const [showConfirm, setShowConfirm] = React.useState(false);
  const [showExport, setShowExport] = React.useState(false);
  const [exportFilename, setExportFilename] = React.useState("个人简介");
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (!user) return;
    api.get("/user/bio").then(({ data }) => {
      if (data.bio) setBio(data.bio);
      if (data.bioVisibility) setBioVisibility(data.bioVisibility);
    }).catch(() => {});
  }, [user]);

  async function handleSave() {
    setSaving(true);
    try {
      await api.post("/user/profile-bio", { bio, bioVisibility });
    } catch {
      // 可加错误提示
    } finally {
      setSaving(false);
    }
  }

  function handleExport() {
    if (!exportFilename.trim()) return;
    const blob = new Blob([bio], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${exportFilename.trim()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setShowExport(false);
  }

  if (loading) return <div className="p-6 text-center text-muted-foreground">加载中...</div>;
  if (!user) return <div className="p-6 text-center text-muted-foreground">请先登录</div>;

  return (
    <div className="p-6 bg-white dark:bg-zinc-900 rounded-lg shadow-sm">
      <h2 className="text-2xl font-bold mb-4">我的履历</h2>
      <section>
        <div className="mb-3 flex items-center gap-4">
          <label className="font-normal text-sm">是否仅自己可见：</label>
          <select
            value={bioVisibility}
            onChange={e => setBioVisibility(e.target.value as "private" | "public")}
            className="border rounded px-2 py-1 text-sm"
          >
            <option value="private">仅自己可见</option>
            <option value="public">所有人可见</option>
          </select>
        </div>
        <MarkdownEditor
          value={bio}
          onChange={setBio}
          placeholder="请输入个人简介，支持Markdown语法"
          preview={true}
          theme="light"
        />
        <div className="flex gap-2 mt-4">
          <Button onClick={() => setShowConfirm(true)} disabled={saving}>
            {saving ? "保存中..." : "保存"}
          </Button>
          <Button variant="outline" onClick={() => { setExportFilename("个人简介"); setShowExport(true); }}>
            导出
          </Button>
        </div>
      </section>

      <Modal
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        title="确认保存"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowConfirm(false)}>取消</Button>
            <Button onClick={() => { setShowConfirm(false); handleSave(); }}>确定</Button>
          </>
        }
      >
        <p>确定要保存当前的修改内容吗？</p>
      </Modal>

      <Modal
        open={showExport}
        onClose={() => setShowExport(false)}
        title="导出文件"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowExport(false)}>取消</Button>
            <Button onClick={handleExport}>确认导出</Button>
          </>
        }
      >
        <p className="mb-2">文件后缀默认为 <code className="rounded bg-muted px-1 text-xs">.md</code></p>
        <input
          type="text"
          value={exportFilename}
          onChange={e => setExportFilename(e.target.value)}
          placeholder="请输入文件名"
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-3 focus:ring-ring/50"
          autoFocus
        />
      </Modal>
    </div>
  );
}
