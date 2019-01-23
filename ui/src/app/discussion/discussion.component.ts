import { Component, OnInit } from '@angular/core';
import { Discussion } from '../models';

@Component({
  selector: 'app-discussion',
  templateUrl: './discussion.component.html',
  styleUrls: ['./discussion.component.css']
})
export class DiscussionComponent implements OnInit {

  discussion: Discussion = {
    id: 2,
    title: 'Java Code Review: Get Access Tokens from external Acme Service',
    body: 'This is the body of java code review. This is a `variable` ',
    author: 'sripathi.krishnan',
    team: 'tech',
    submissionTime: 432323223232,
    comments: [
      {
        id: 1,
        body: 'This _is_ in *markdown*',
        author: 'sripathi.krishnan',
        submissionTime: 432323223232,
        indent: 0
      },
      {
        id: 2,
        body: 'This is the reply, also in markdown. The opposite of *markup*',
        author: 'sripathi.krishnan',
        submissionTime: 432323223232,
        indent: 1
      }
    ]
  };
  constructor() { }

  ngOnInit() {
  }
}
