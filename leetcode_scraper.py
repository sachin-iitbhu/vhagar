# leetcode_scraper.py
# This script scrapes LeetCode compensation data using their GraphQL APIs
# It fetches compensation topics and their detailed content for RAG Agent

import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Optional

class LeetCodeCompensationScraper:
    def __init__(self):
        self.base_url = "https://leetcode.com/graphql/"
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.7",
            "authorization": "",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "sec-ch-ua": '"Chromium";v="136", "Brave";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1"
        }
        
        # GraphQL queries
        self.topics_query = """
        query discussPostItems($orderBy: ArticleOrderByEnum, $keywords: [String]!, $tagSlugs: [String!], $skip: Int, $first: Int) {
          ugcArticleDiscussionArticles(
            orderBy: $orderBy
            keywords: $keywords
            tagSlugs: $tagSlugs
            skip: $skip
            first: $first
          ) {
            totalNum
            pageInfo {
              hasNextPage
            }
            edges {
              node {
                uuid
                title
                slug
                summary
                author {
                  realName
                  userAvatar
                  userSlug
                  userName
                  nameColor
                }
                createdAt
                updatedAt
                topicId
                hitCount
                tags {
                  name
                  slug
                  tagType
                }
                topic {
                  id
                  topLevelCommentCount
                }
              }
            }
          }
        }
        """
        
        self.detail_query = """
        query discussPostDetail($topicId: ID!) {
          ugcArticleDiscussionArticle(topicId: $topicId) {
            uuid
            title
            slug
            summary
            content
            author {
              realName
              userAvatar
              userSlug
              userName
              nameColor
            }
            createdAt
            updatedAt
            topicId
            hitCount
            tags {
              name
              slug
              tagType
            }
            topic {
              id
              topLevelCommentCount
            }
          }
        }
        """

    async def fetch_compensation_topics(self, session: aiohttp.ClientSession, skip: int = 0, first: int = 50) -> Optional[Dict]:
        """Fetch compensation topics from LeetCode GraphQL API"""
        payload = {
            "query": self.topics_query,
            "variables": {
                "orderBy": "HOT",
                "keywords": ["compensation"],  # Filter for compensation posts
                "tagSlugs": [],
                "skip": skip,
                "first": first
            },
            "operationName": "discussPostItems"
        }
        
        try:
            async with session.post(self.base_url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Failed to fetch topics: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching topics: {str(e)}")
            return None

    async def fetch_post_detail(self, session: aiohttp.ClientSession, topic_id: str) -> Optional[Dict]:
        """Fetch detailed content for a specific topic"""
        payload = {
            "query": self.detail_query,
            "variables": {
                "topicId": topic_id
            },
            "operationName": "discussPostDetail"
        }
        
        try:
            async with session.post(self.base_url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Failed to fetch detail for topic {topic_id}: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching detail for topic {topic_id}: {str(e)}")
            return None

    async def scrape_all_compensation_data(self, max_posts: int = 10000) -> List[Dict]:
        """Scrape compensation data from LeetCode"""
        all_compensation_data = []
        
        async with aiohttp.ClientSession() as session:
            skip = 0
            batch_size = 50
            
            print(f"Starting to scrape up to {max_posts} compensation posts...")
            
            while len(all_compensation_data) < max_posts:
                print(f"Fetching topics batch: {skip} to {skip + batch_size}")
                
                # Fetch topic list
                topics_data = await self.fetch_compensation_topics(session, skip, batch_size)
                if not topics_data or not topics_data.get('data'):
                    print("No more topics found or API error")
                    break
                
                articles = topics_data['data']['ugcArticleDiscussionArticles']['edges']
                if not articles:
                    print("No articles in this batch")
                    break
                
                # Process each topic
                for article in articles:
                    if len(all_compensation_data) >= max_posts:
                        break
                        
                    node = article['node']
                    topic_id = node['topicId']
                    
                    # Check if it's compensation related
                    title = node['title'].lower()
                    if not any(keyword in title for keyword in ['compensation', 'salary', 'offer', 'pay', 'total comp']):
                        continue
                    
                    print(f"Fetching details for: {node['title'][:50]}...")
                    
                    # Fetch detailed content
                    detail_data = await self.fetch_post_detail(session, topic_id)
                    if detail_data and detail_data.get('data'):
                        article_detail = detail_data['data']['ugcArticleDiscussionArticle']
                        
                        # Combine topic info with detailed content
                        compensation_post = {
                            'topic_id': topic_id,
                            'title': article_detail['title'],
                            'summary': article_detail['summary'],
                            'content': article_detail['content'],
                            'author': article_detail['author']['userName'] if article_detail['author'] else 'Anonymous',
                            'created_at': article_detail['createdAt'],
                            'updated_at': article_detail['updatedAt'],
                            'hit_count': article_detail['hitCount'],
                            'tags': [tag['name'] for tag in article_detail['tags']],
                            'url': f"https://leetcode.com/discuss/post/{topic_id}",
                            'scraped_at': time.time()
                        }
                        
                        all_compensation_data.append(compensation_post)
                        print(f"Scraped post {len(all_compensation_data)}: {compensation_post['title'][:50]}...")
                    
                    # Be respectful to the API
                    await asyncio.sleep(0.5)
                
                skip += batch_size
                
                # Check if there are more pages
                has_next_page = topics_data['data']['ugcArticleDiscussionArticles']['pageInfo']['hasNextPage']
                if not has_next_page:
                    print("No more pages available")
                    break
                
                # Longer delay between batches
                await asyncio.sleep(2)
            
        return all_compensation_data

async def main():
    """Main function to run the scraper and save results"""
    print("Starting LeetCode compensation data scraping via GraphQL API...")
    
    # Create scraper instance
    scraper = LeetCodeCompensationScraper()
    
    # Scrape compensation data
    compensation_data = await scraper.scrape_all_compensation_data(max_posts=1000)
    
    if compensation_data:
        # Save to JSON file
        with open("leetcode_compensation_data.json", "w", encoding='utf-8') as f:
            json.dump(compensation_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nScraping completed!")
        print(f"Total compensation posts scraped: {len(compensation_data)}")
        print(f"Data saved to: leetcode_compensation_data.json")
        
        # Print sample data
        if compensation_data:
            print("\nSample compensation post:")
            sample = compensation_data[0]
            print(f"Title: {sample['title']}")
            print(f"Author: {sample['author']}")
            print(f"Created: {sample['created_at']}")
            print(f"Content preview: {sample['content'][:200]}...")
            print(f"Tags: {sample['tags']}")
    else:
        print("No compensation data was scraped.")

if __name__ == "__main__":
    # Run the async scraper
    asyncio.run(main())
