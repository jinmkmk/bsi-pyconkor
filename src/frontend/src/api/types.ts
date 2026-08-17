export interface School {
  officeCode: string;
  schoolCode: string;
  name: string;
  region: string;
  schoolType: string;
  address: string;
}

export interface SchoolPage {
  items: School[];
  totalCount: number;
  page: number;
  pageSize: number;
}

export interface Meal {
  date: string;
  mealType: "중식";
  dishes: string[];
  calories?: string | null;
  nutrition?: string | null;
}

export interface MealPage {
  school: Pick<School, "officeCode" | "schoolCode" | "name">;
  from: string;
  to: string;
  items: Meal[];
}
