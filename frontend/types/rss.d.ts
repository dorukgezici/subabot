type Feed = {
  key: string;
  title: string;
  url: string;

  refreshed_at: number | null;
  data: JSON | null;
};

type Keyword = {
  key: string;
  value: string;

  checked_at: number | null;
  matches: JSON;
};
