export class Topic {
  id: Number;
  title: String;
  author: String;
  team: String;
  numComments: Number;
  submissionTime: Number;
  isRead: Boolean;
}

export interface Comment {
  id: Number;
  body: String;
  author: String;
  submissionTime: Number;
  indent: Number;
}

export class Discussion {
  id: Number;
  title: String;
  body: String;
  author: String;
  team: String;
  submissionTime: Number;
  comments: Array<Comment>;
}
