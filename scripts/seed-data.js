// MongoDB seed script - inserts sample menu items if collection is empty
// Usage: mongosh --host mongo:27017 -u root -p rootpassword --authenticationDatabase admin food-delivery scripts/seed-data.js

const menuItems = [
  {
    name: "Margherita Pizza",
    description: "Classic tomato sauce, mozzarella, and fresh basil",
    price: 12.99,
    category: "pizza",
    stock: 200,
  },
  {
    name: "Pepperoni Pizza",
    description: "Tomato sauce, mozzarella, and spicy pepperoni",
    price: 14.99,
    category: "pizza",
    stock: 200,
  },
  {
    name: "Hawaiian Pizza",
    description: "Tomato sauce, mozzarella, ham, and pineapple",
    price: 13.99,
    category: "pizza",
    stock: 200,
  },
  {
    name: "Coca-Cola",
    description: "Classic refreshing cola, 330ml",
    price: 2.99,
    category: "drinks",
    stock: 500,
  },
  {
    name: "Sparkling Water",
    description: "Naturally carbonated mineral water, 500ml",
    price: 1.99,
    category: "drinks",
    stock: 500,
  },
  {
    name: "Lava Cake",
    description: "Warm chocolate cake with a molten center",
    price: 7.99,
    category: "desserts",
    stock: 150,
  },
  {
    name: "Tiramisu",
    description: "Classic Italian coffee-flavored dessert",
    price: 6.99,
    category: "desserts",
    stock: 150,
  },
];

const existing = db.menu_items.countDocuments();
if (existing === 0) {
  db.menu_items.insertMany(menuItems);
  print(`Inserted ${menuItems.length} menu items.`);
} else {
  print(`Collection already has ${existing} items, skipping seed.`);
}
