import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { DiscussionComponent } from './discussion/discussion.component';
import { TopicsComponent } from './topics/topics.component';

const routes: Routes = [
  {path: '', component: TopicsComponent},
  {path: 'discuss/:id', component: DiscussionComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
