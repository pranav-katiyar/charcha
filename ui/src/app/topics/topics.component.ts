import { Component, OnInit } from '@angular/core';
import { Topic } from '../models';

@Component({
  selector: 'app-topics',
  templateUrl: './topics.component.html',
  styleUrls: ['./topics.component.css']
})
export class TopicsComponent implements OnInit {
  topics: Array<Topic> = [
    {
      'id': 1,
      'title': 'For Developers: How do you start learning AWS?',
      'author': 'sripathi.krishnan',
      'team': 'general',
      'numComments': 0,
      'submissionTime': 3213132123333,
      'isRead': true
    },
    {
      'id': 2,
      'title': 'Authentication of requests from website to server',
      'author': 'renjith.s',
      'team': 'tech',
      'numComments': 3,
      'submissionTime': 3213132123,
      'isRead': true
    },
    {
      'id': 3,
      'title': 'MySQL didn\'t pick up an index until we executed a dummy alter table statement. Why?',
      'author': 'nikhil.satish',
      'team': 'tech',
      'numComments': 3,
      'submissionTime': 3213132123,
      'isRead': false
    },
    {
      'id': 4,
      'title': 'RestTemplate - Sample Code',
      'author': 'sripathi.krishnan',
      'team': 'tech',
      'numComments': 7,
      'submissionTime': 3213132123,
      'isRead': true
    },
    {
      'id': 5,
      'title': 'Java Code Review: Get Access Tokens from external Acme Service',
      'author': 'sripathi.krishnan',
      'team': 'tech',
      'numComments': 13,
      'submissionTime': 3213132123,
      'isRead': false
    },
    {
      'id': 6,
      'title': 'Automated Testing: Build a DSL - Twitter Example',
      'author': 'sripathi.krishnan',
      'team': 'tech',
      'numComments': 0,
      'submissionTime': 3213132123,
      'isRead': false
    }
  ];
  constructor() { }

  ngOnInit() {
  }

}
