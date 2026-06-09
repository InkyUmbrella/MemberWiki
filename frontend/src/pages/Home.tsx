import { useEffect, useState } from "react";
import MDEditor from "@uiw/react-md-editor";
import api from "@/lib/api";

interface MemberItem {
  profile_id: number;
  user_name: string;
  bio_highlight: string;
  award_count: number;
  updated_at: string;
}

export default function Home() {
  const [members, setMembers] = useState<MemberItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/search/members")
      .then(({ data }) => setMembers(data.items ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 bg-white dark:bg-zinc-900 rounded-lg shadow-sm">
      <h2 className="text-2xl font-bold mb-4">名人堂检索</h2>
      {loading ? (
        <p className="text-muted-foreground">加载中...</p>
      ) : members.length === 0 ? (
        <p className="text-muted-foreground">暂无可公开的个人简介</p>
      ) : (
        <div className="grid gap-4">
          {members.map((member) => (
            <div key={member.profile_id} className="rounded-lg border border-border p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                  {member.user_name.charAt(0)}
                </div>
                <span className="font-medium">{member.user_name}</span>
                {member.award_count > 0 && (
                  <span className="text-xs text-muted-foreground ml-auto">{member.award_count} 个奖项</span>
                )}
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <MDEditor.Markdown source={member.bio_highlight} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
