import { useEffect, useState } from "react";
import MDEditor from "@uiw/react-md-editor";
import api from "@/lib/api";

interface PublicBio {
  userId: string;
  username: string;
  avatar?: string;
  bio: string;
}

export default function Home() {
  const [users, setUsers] = useState<PublicBio[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/users/public-bios")
      .then(({ data }) => setUsers(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 bg-white dark:bg-zinc-900 rounded-lg shadow-sm">
      <h2 className="text-2xl font-bold mb-4">名人堂检索</h2>
      {loading ? (
        <p className="text-muted-foreground">加载中...</p>
      ) : users.length === 0 ? (
        <p className="text-muted-foreground">暂无可公开的个人简介</p>
      ) : (
        <div className="grid gap-4">
          {users.map((user) => (
            <div key={user.userId} className="rounded-lg border border-border p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                  {user.username.charAt(0)}
                </div>
                <span className="font-medium">{user.username}</span>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <MDEditor.Markdown source={user.bio} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
