"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Niche } from "@/lib/types";

interface NicheSelectorProps {
  niches: Niche[];
  selected: string;
  onSelect: (slug: string) => void;
}

export function NicheSelector({
  niches,
  selected,
  onSelect,
}: NicheSelectorProps) {
  return (
    <Select value={selected} onValueChange={onSelect}>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a niche" />
      </SelectTrigger>
      <SelectContent>
        {niches.map((niche) => (
          <SelectItem key={niche.slug} value={niche.slug}>
            {niche.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
