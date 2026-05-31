import React from "react";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export default function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  className,
}: ModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative w-full max-w-md mx-4 rounded-lg border border-border bg-background p-6 shadow-xl",
          className,
        )}
      >
        <h3 className="mb-4 text-lg font-semibold text-foreground">{title}</h3>
        <div className="text-sm text-muted-foreground">{children}</div>
        {footer && (
          <div className="mt-6 flex items-center justify-end gap-2">{footer}</div>
        )}
      </div>
    </div>
  );
}
